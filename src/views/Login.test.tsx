// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import Login from "./Login";

vi.mock("../auth/AuthProvider", () => ({
  useAuth: () => ({
    requestMagicLink: vi.fn(),
    completeMagicLink: vi.fn(),
    requestedEmail: "operator@example.com",
    lastMagicLink: "dev-token-123",
    loading: false,
  }),
}));

describe("Login", () => {
  it("renders the cloud login surface", () => {
    render(<Login />);

    expect(screen.getByText("Operator Sign In")).toBeTruthy();
    expect(screen.getByText("Magic Link Token")).toBeTruthy();
    expect(screen.getByText("Development token")).toBeTruthy();
    expect(screen.getByText("dev-token-123")).toBeTruthy();
  });
});
