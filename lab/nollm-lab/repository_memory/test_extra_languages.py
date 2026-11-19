import unittest

from extra_languages import parse_extra
from facts import source_text


class LanguageDeclarations(unittest.TestCase):
    def facts(self, lang, body):
        symbols, edges = [], []
        files = {"pkg/app.js":{"mode":"100644"},"pkg/theme.css":{"mode":"100644"}}
        parse_extra(lang,"pkg/input",body,files,lambda *r:symbols.append(r),lambda *r:edges.append(r),lambda *r:None)
        return {(n,kind,name,qual) for n,_,kind,name,qual in symbols}, edges

    def test_javascript_masks_strings_comments_templates_and_regex(self):
        code = """/* function bogus() {} */
// class Another {}
const sample = `ignored ${`nested\nfunction Wrong() {}`}\nclass AlsoWrong {}\n`;
const expr = /[{};]function fake\\(\\)/;
const label = "function literal() {}";
export async function start () {}
function* items() {}
class Market extends Map {}
"""
        syms, edges = self.facts("javascript", code)
        self.assertEqual({(kind,name) for _,kind,name,_ in syms}, {
            ("js_function_candidate","start"),("js_function_candidate","items"),("js_class_candidate","Market")})
        self.assertEqual(sorted(s[0] for s in syms),[9,10,11])
        self.assertEqual(edges,[])
        conditional = "if (active && check()) /;function Phantom(){}|class AlsoWrong{}/.test(source);"
        self.assertEqual(self.facts("javascript", conditional)[0], set())

    def test_arrow_variables_follow_declaration_lists_and_keep_name_lines(self):
        code = """export const initial = [1, 2], $pick = (value, fallback = build(1, 2)) => value || fallback,
 asyncMap = async ({key}, [value]) => await work(key, value);
let count, twice = item => item * 2;
var {a, b} = source, halve = async => async / 2;
const split =
    () => true;
"""
        syms, _ = self.facts("javascript", code)
        self.assertEqual({(line, name) for line, kind, name, _ in syms if kind == "js_arrow_binding_candidate"},
                         {(1, "$pick"), (2, "asyncMap"), (3, "twice"), (4, "halve"), (5, "split")})

    def test_arrow_variables_reject_calls_literals_assignments_and_asi(self):
        code = """const called = map(x => x), result = ((x) => x)(20);
const expression = use(1, assigned = x => x);
const cond = on ? x => x : y => y;
const literal = "const fake = y => y";
const pattern = /let fail = x => x/;
const template = `var hidden = () => 7`;
/* const ghost = () => 0; */
let sentinel = 1
ordinary, reassign = x => x;
const stringOperand = "a"
x => x;
const maybeAsync = async
arg => arg;
({ property: p => p }); instance.property = x => x;
const actual = x => [1, 2].map(y => y + x);
"""
        syms, _ = self.facts("javascript", code)
        self.assertEqual({name for _, kind, name, _ in syms if kind == "js_arrow_binding_candidate"},
                         {"actual"})

    def test_powershell_masks_here_strings_nesting_comments_commands(self):
        code = """<#
function Ghost {}
<# class AlsoFalse {} #>
#>
$note = @'
function NotACommand {}
'@
$note = "function InQuote {}"
Write-Output function Noise
function script:Get-Status {
}
filter Read-Value($item) {}
enum Mode { A; B }
"""
        syms, _ = self.facts("powershell", code)
        self.assertEqual(syms,{(10,"ps_function_candidate","script:Get-Status","script:Get-Status"),
                              (12,"ps_filter_candidate","Read-Value","Read-Value"),(13,"ps_enum_candidate","Mode","Mode")})

    def test_unicode_bom_shell_input(self):
        example = "# 接手脚本\nfunction Read-Data {}\n"
        for encoding in ("utf-16", "utf-32", "utf-8-sig"):
            self.assertEqual(self.facts("powershell",source_text(example.encode(encoding)))[0],
                             {(2,"ps_function_candidate","Read-Data","Read-Data")})

    def test_sql_quoted_names_comments_ddl_bodies_and_strings(self):
        code = """-- CREATE TABLE hidden_1(x);
SELECT 'CREATE TABLE hidden_2(x);';
CREATE TABLE IF NOT EXISTS main."prices"
 (symbol TEXT);
CREATE FUNCTION public.f() RETURNS void AS $$
 CREATE TABLE hidden_3(x);
$$ LANGUAGE sql;
/* CREATE TRIGGER hidden_4... */
CREATE UNIQUE INDEX prices_ix ON prices(symbol);
"""
        syms, _ = self.facts("sql", code)
        self.assertEqual(syms,{(3,"sql_table_candidate","prices","main.prices"),(5,"sql_function_candidate","f","public.f"),
                               (9,"sql_index_candidate","prices_ix","prices_ix")})

    def test_html_multiline_assets_comments_script_content_and_base(self):
        code = """<!-- <i id="ghost"> -->
<div title="id='bogus'"
 id="orders"></div>
<script src="./app.js?q=1">"<div id='ghost'>"</script>
<link rel="stylesheet" href="theme.css" />
"""
        syms, edges = self.facts("html", code)
        self.assertEqual(syms,{(3,"html_id_candidate","orders","orders")})
        self.assertEqual(edges,[("pkg/app.js",4,"html_relative_asset","candidate","./app.js"),
                                ("pkg/theme.css",5,"html_relative_asset","candidate","theme.css")])
        self.assertEqual(self.facts("html",code+'<base href="/elsewhere/">')[1], [])

    def test_css_declarations_and_false_friends(self):
        code = '''/* @keyframes fake {} */
:root { --ink: red; content: "@keyframes ghost {}"; }
@keyframes bounce { from { opacity: 0; } to { opacity: 1; } }
'''
        syms, _ = self.facts("css",code)
        self.assertEqual(syms,{(2,"css_custom_property_candidate","--ink","--ink"),(3,"css_keyframes_candidate","bounce","bounce")})


if __name__ == "__main__":
    unittest.main()
