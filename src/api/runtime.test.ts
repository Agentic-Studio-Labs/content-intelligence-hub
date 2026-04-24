import { describe, expect, it } from "vitest";

import { getBackendInfo } from "./runtime";

describe("runtime defaults", () => {
  it("defaults to local backend mode", () => {
    expect(getBackendInfo()).toEqual({
      mode: "local",
      baseUrl: "http://localhost:8420",
      authRequired: false,
    });
  });
});
