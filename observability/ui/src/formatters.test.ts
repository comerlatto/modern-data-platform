import assert from "node:assert/strict";
import test from "node:test";
import { duration, formatDate, relativeDuration } from "./formatters.ts";

test("converte UTC para America/Sao_Paulo", () => {
  assert.equal(formatDate("2026-08-14T12:38:42.839087+00:00"), "14/08/2026 às 09:38");
});

test("formata durações sem acumular minutos", () => {
  assert.equal(duration(47), "47 s");
  assert.equal(duration(107), "1 min 47 s");
  assert.equal(duration(4080), "1 h 8 min");
  assert.equal(relativeDuration(172800), "há 2 d");
});
