"""Conservative lexical witnesses for declarations outside Python and native builds."""
from __future__ import annotations

from bisect import bisect_right
from html.parser import HTMLParser
import posixpath
import re
from urllib.parse import urlsplit

EXTRA_LANGUAGES = {"javascript", "powershell", "sql", "html", "css"}
JS_ID = r"[A-Za-z_$][A-Za-z_$0-9]*"
SQL_ID = r"[A-Za-z_][A-Za-z_0-9$]*"
PS_ID = r"(?:(?:global|local|script|private):)?[A-Za-z_][A-Za-z0-9_-]*"


def line_starts(text):
    return [0, *(match.end() for match in re.finditer("\n", text))]


def mask_span(target, text, start, end):
    target[start:end] = re.sub(r"[^\n]", " ", text[start:end])


def skip_string(text, start, quote, escape="\\", doubled=False):
    i = start + 1
    while i < len(text):
        if escape and text[i] == escape:
            i += 2
        elif text[i] == quote:
            if doubled and text[i+1:i+2] == quote:
                i += 2
            else:
                return i + 1
        else:
            i += 1
    return len(text)


def through(text, needle, start):
    end = text.find(needle, start)
    return len(text) if end < 0 else end + len(needle)


def skip_js_regex(text, start):
    char_class = False
    i = start + 1
    while i < len(text) and text[i] not in "\r\n":
        ch = text[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "[":
            char_class = True
        elif ch == "]":
            char_class = False
        elif ch == "/" and not char_class:
            return i + 1
        i += 1
    return start + 1


def skip_template(text, start):
    # Shield the complete template including nested templates and interpolation.
    i = start + 1
    expr_depth = 0
    while i < len(text):
        c = text[i]
        if c == "\\":
            i += 2
        elif not expr_depth and c == "`":
            return i + 1
        elif not expr_depth and text.startswith("${", i):
            expr_depth, i = 1, i + 2
        elif expr_depth and c in {"'", '"'}:
            i = skip_string(text, i, c)
        elif expr_depth and c == "`":
            i = skip_template(text, i)
        elif expr_depth and text.startswith("//", i):
            i = through(text, "\n", i + 2)
        elif expr_depth and text.startswith("/*", i):
            i = through(text, "*/", i + 2)
        else:
            if expr_depth:
                expr_depth += (c == "{") - (c == "}")
            i += 1
    return len(text)


def shield_js(text):
    out = list(text)
    i = 0
    last = ""
    statement_parens = []
    while i < len(text):
        c = text[i]
        literal = False
        if text.startswith("//", i):
            j = through(text, "\n", i + 2)
        elif text.startswith("/*", i):
            j = through(text, "*/", i + 2)
        elif c in {"'", '"', "`"}:
            j = skip_template(text, i) if c == "`" else skip_string(text, i, c)
            literal = True
            last = "literal"
        elif c == "/" and (not last or last in REGEX_PREFIX):
            j = skip_js_regex(text, i)
            if j == i + 1:
                last, i = c, i + 1
                continue
            literal = True
            last = "literal"
        else:
            if c in "_$" or c.isascii() and c.isalpha():
                match = JS_IDENTIFIER.match(text, i)
                last, i = match.group(), match.end()
            else:
                if c == "(":
                    statement_parens.append(last in {"if", "while", "for", "with"})
                if c == ")" and statement_parens:
                    last = "statement_body" if statement_parens.pop() else c
                elif not c.isspace():
                    last = c
                i += 1
            continue
        mask_span(out, text, i, j)
        if literal:
            out[i] = "0"  # Keep an operand boundary for declaration/ASI detection.
        i = j
    return "".join(out)


REGEX_PREFIX = set("=([{!?:;,|&~<>+*%-") | {"return","case","yield","throw","typeof","void","delete","statement_body"}
JS_IDENTIFIER = re.compile(JS_ID)
JS_DECL = re.compile(rf"(?:^|(?<=[;{{}}]))[ \t]*(?:(?:export|default|async)\s+)*(?P<kind>function\b\s*\*?\s*|class\s+)(?P<name>{JS_ID})\b", re.M)


JS_TOKEN = re.compile(rf"{JS_ID}|(?:=>|\?\.|\+\+|--)|[^\s]")
JS_CLOSE = {"(": ")", "[": "]", "{": "}"}


def arrow_bindings(code):
    """Find directly arrow-valued declarators. Skip compound expressions as units."""
    tokens = list(JS_TOKEN.finditer(code))
    words = [token.group() for token in tokens]
    pairs, stack = {}, []
    for i, word in enumerate(words):
        if word in JS_CLOSE:
            stack.append(i)
        elif stack and word == JS_CLOSE[words[stack[-1]]]:
            pairs[stack.pop()] = i

    def newline(before, after):
        return bool(re.search(r"[\r\n\u2028\u2029]", code[tokens[before].end():tokens[after].start()]))

    def arrow_head(start):
        # Async is also a legal single parameter, as in `async => async`.
        if start + 1 < len(words) and words[start] == "async" and words[start + 1] != "=>":
            if newline(start, start + 1):
                return False
            start += 1
        if start >= len(words):
            return False
        if words[start] == "(" and start in pairs:
            end = pairs[start]
        elif JS_IDENTIFIER.fullmatch(words[start]):
            end = start
        else:
            return False
        return end + 1 < len(words) and words[end + 1] == "=>" and not newline(end, end + 1)

    def next_declarator(start):
        # Only commas at declaration depth can introduce another binding.
        i = start
        while i < len(words):
            word = words[i]
            if word == ",":
                return i + 1
            if word in (";", ")", "]", "}") or word in JS_CLOSE and i not in pairs:
                break
            if i > start and newline(i - 1, i):
                prior = words[i - 1]
                can_finish = JS_IDENTIFIER.fullmatch(prior) or prior.isdecimal() or prior in (")", "]", "}", "++", "--")
                begins_statement = JS_IDENTIFIER.fullmatch(word) and word not in ("in", "instanceof")
                if can_finish and begins_statement:
                    break
            i = pairs.get(i, i) + 1
        return len(words)

    for index, word in enumerate(words):
        if word not in ("const", "let", "var") or (index and words[index - 1] in (".", "?.")):
            continue
        i = index + 1
        while i < len(words):
            if words[i] in ("[", "{") and i in pairs:
                end = pairs[i]  # Destructuring does not bind one name to this RHS.
            elif JS_IDENTIFIER.fullmatch(words[i]):
                end = i
                if i + 2 < len(words) and words[i + 1] == "=" and arrow_head(i + 2):
                    yield tokens[i]
            else:
                break
            i = next_declarator(end + 1)


def parse_javascript(text, symbol):
    code = shield_js(text)
    starts = line_starts(text)
    for m in JS_DECL.finditer(code):
        line = bisect_right(starts, m.start("name"))
        name = m.group("name")
        kind = "js_function_candidate" if m.group("kind").startswith("function") else "js_class_candidate"
        tail = code[m.end("name"):].lstrip()
        if kind == "js_function_candidate" and not tail.startswith("("):
            continue
        if kind == "js_class_candidate" and not (tail.startswith("{") or re.match(r"extends\b", tail)):
            continue
        symbol(line, line, kind, name, name)
    for name in arrow_bindings(code):
        line = bisect_right(starts, name.start())
        symbol(line, line, "js_arrow_binding_candidate", name.group(), name.group())
    return "js_lexical"


PS_DECL = re.compile(rf"(?:^|(?<=[;{{}}]))[ \t]*(?P<kind>function|filter|workflow|class|enum)\s+(?P<name>{PS_ID})[ \t\r\n]*(?=[({{:])", re.I | re.M)


def parse_powershell(text, symbol):
    masked = list(text)
    i = 0
    while i < len(text):
        c = text[i]
        if text.startswith("<#", i):
            depth, j = 1, i + 2
            while depth and j < len(text):
                if text.startswith("<#", j):
                    depth, j = depth + 1, j + 2
                elif text.startswith("#>", j):
                    depth, j = depth - 1, j + 2
                else:
                    j += 1
        elif c == "#":
            j = through(text, "\n", i + 1)
        elif text[i:i+2] in {"@'", '@"'} and re.match(r"[^\S\n]*\n", text[i+2:]):
            quote = text[i+1]
            closing = re.compile("^" + re.escape(quote + "@"), re.M).search(text, i + 2)
            j = closing.end() if closing else len(text)
        elif c in {"'", '"'}:
            j = skip_string(text, i, c, escape="`" if c == '"' else "", doubled=True)
        elif c == "`":
            j = min(i + 2, len(text))
        else:
            i += 1
            continue
        mask_span(masked, text, i, j)
        i = j
    starts = line_starts(text)
    for m in PS_DECL.finditer("".join(masked)):
        line = bisect_right(starts, m.start("name"))
        kind = "ps_" + m.group("kind").lower() + "_candidate"
        symbol(line, line, kind, m.group("name"), m.group("name"))
    return "ps_lexical"


SQL_TOKEN = re.compile(
    r"""(?P<skip>\s+|--[^\n]*|\#[^\n]*|/\*.*?(?:\*/|\Z)|\$(?P<tag>[A-Za-z_]\w*|)\$.*?\$(?P=tag)\$|'(?:''|\\.|[^'])*(?:'|\Z))"""
    r"""|(?P<quoted>"(?:""|[^"])*"|`(?:``|[^`])*`|\[[^\]]*\])|(?P<word>[A-Za-z_][\w$]*)|(?P<other>.)""",
    re.S,
)
SQL_KIND = {"TABLE","VIEW","INDEX","TRIGGER","FUNCTION","PROCEDURE","SCHEMA","SEQUENCE","TYPE"}


def parse_sql(text, symbol):
    toks = [m for m in SQL_TOKEN.finditer(text) if m.lastgroup != "skip"]
    starts = line_starts(text)
    for k,t in enumerate(toks):
        if t.lastgroup != "word" or t.group().upper() != "CREATE":
            continue
        if k and toks[k-1].group() != ";":
            continue
        i = k + 1
        while i < len(toks) and toks[i].lastgroup == "word" and toks[i].group().upper() in {"OR","REPLACE","TEMP","TEMPORARY","MATERIALIZED","UNIQUE","VIRTUAL"}:
            i += 1
        if i >= len(toks) or toks[i].lastgroup != "word" or toks[i].group().upper() not in SQL_KIND:
            continue
        kind = toks[i].group().lower()
        i += 1
        if [u.group().upper() for u in toks[i:i+3]] == ["IF","NOT","EXISTS"]:
            i += 3
        names = []
        while i < len(toks) and toks[i].lastgroup in {"word", "quoted"}:
            token = toks[i]
            value = token.group()
            if token.lastgroup == "quoted":
                value = value[1:-1]
            if not re.fullmatch(SQL_ID, value):
                break
            names.append(value)
            i += 1
            if i >= len(toks) or toks[i].group() != ".":
                break
            i += 1
        if names:
            line = bisect_right(starts, token.start())
            symbol(line,line,"sql_" + kind + "_candidate",names[-1],".".join(names))
    return "sql_lexical"


CSS_SHIELD = re.compile(r"""/\*.*?(?:\*/|\Z)|"(?:\\.|[^"\\])*(?:"|\Z)|'(?:\\.|[^'\\])*(?:'|\Z)""", re.S)
CSS_DECL = re.compile(r"(?:(?P<key>@(?:-webkit-)?keyframes|@property)\s+(?P<name>[\w-]+)\s*\{|(?<=[{;])\s*(?P<custom>--[\w-]+)\s*:)")


def parse_css(text, symbol):
    code = CSS_SHIELD.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), text)
    starts = line_starts(text)
    for m in CSS_DECL.finditer(code):
        group = "custom" if m.group("custom") else "name"
        name = m.group(group)
        kind = "css_custom_property_candidate" if group == "custom" or m.group("key") == "@property" else "css_keyframes_candidate"
        line = bisect_right(starts,m.start(group))
        symbol(line,line,kind,name,name)
    return "css_lexical"


HTML_ATTR = re.compile(r"""\s+([^\s="'<>/]+)(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'=<>\x60]+))?""")
HTML_TAG = re.compile(r"<[^\s/>]+")


class HTMLFacts(HTMLParser):
    def __init__(self, path, files, symbol, edge):
        super().__init__(convert_charrefs=True)
        self.path, self.files, self.symbol, self.edge = path, files, symbol, edge
        self.uses_base = False
        self.targets = []

    def handle_starttag(self, tag, attrs):
        raw = self.get_starttag_text()
        base_line = self.getpos()[0]
        lines = [base_line + raw.count("\n", 0, m.start(1)) for m in HTML_ATTR.finditer(raw, HTML_TAG.match(raw).end())]
        if len(lines) != len(attrs):
            return
        pairs = dict(attrs)
        for (name, value), line in zip(attrs, lines):
            if not value:
                continue
            if name == "id" and re.fullmatch(r"[\w.-]+", value):
                self.symbol(line, line, "html_id_candidate", value, value)
            if tag == "base" and name == "href":
                self.uses_base = True
            if (tag, name) == ("script", "src") or (tag,name) == ("link","href") and "stylesheet" in (pairs.get("rel") or "").lower().split():
                self.targets.append((line, value))

    def finish(self):
        if self.uses_base:
            return
        for line, value in self.targets:
            try:
                target = urlsplit(value)
            except ValueError:
                continue
            if target.scheme or target.netloc or not target.path or target.path.startswith("/") or "%" in target.path:
                continue
            path = posixpath.normpath(posixpath.join(posixpath.dirname(self.path),target.path))
            if path in self.files and self.files[path]["mode"] in {"100644","100755"}:
                self.edge(path,line,"html_relative_asset","candidate",target.path)


def parse_extra(lang, path, text, files, symbol, edge, diagnostic):
    if lang == "html":
        parser = HTMLFacts(path, files, symbol, edge)
        try:
            parser.feed(text)
            parser.close()
        except (AssertionError, ValueError) as exc:
            diagnostic("html_parse_error", parser.getpos()[0], type(exc).__name__)
            return "html_partial"
        parser.finish()
        return "html_parser"
    parser = {"javascript":parse_javascript, "sql":parse_sql, "powershell":parse_powershell, "css":parse_css}[lang]
    return parser(text, symbol)
