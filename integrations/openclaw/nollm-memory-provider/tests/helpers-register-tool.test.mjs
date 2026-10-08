import assert from "node:assert/strict";
import { test } from "node:test";
import { makeMockApi } from "./helpers.mjs";

test("mock registerTool preserves factory/options references and registration order", () => {
  const api = makeMockApi();
  const firstFactory = () => assert.fail("registration must not execute a factory");
  const secondFactory = () => assert.fail("registration must not execute a factory");
  const firstOptions = { names: ["memory_search"] };
  const secondOptions = { names: ["memory_get"] };

  api.registerTool(firstFactory, firstOptions);
  api.registerTool(secondFactory, secondOptions);

  assert.equal(api._events.tools.length, 2);
  assert.equal(api._events.tools[0].factory, firstFactory);
  assert.equal(api._events.tools[0].options, firstOptions);
  assert.equal(api._events.tools[1].factory, secondFactory);
  assert.equal(api._events.tools[1].options, secondOptions);
});

test("mock registerTool only records values and keeps instances independent", () => {
  const api = makeMockApi();
  const otherApi = makeMockApi();
  const factory = new Proxy(() => assert.fail("factory must remain uncalled"), {
    get() { assert.fail("factory properties must not be read"); },
    apply() { assert.fail("factory must remain uncalled"); },
  });
  const options = new Proxy({}, {
    get() { assert.fail("options properties must not be read"); },
  });

  api.registerTool(factory, options);
  api.registerTool(factory);

  assert.equal(api._events.tools[0].factory, factory);
  assert.equal(api._events.tools[0].options, options);
  assert.equal(api._events.tools[1].factory, factory);
  assert.equal(api._events.tools[1].options, undefined);
  assert.equal(otherApi._events.tools, undefined);
});
