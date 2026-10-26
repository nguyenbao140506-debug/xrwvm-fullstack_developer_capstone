import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import Register from "./Register.jsx";

describe("Register", () => {
  it("shows all five labeled fields and a Register button", () => {
    render(<Register />);
    expect(screen.getByLabelText("Username")).toHaveAttribute("name", "username");
    expect(screen.getByLabelText("First Name")).toHaveAttribute("name", "first_name");
    expect(screen.getByLabelText("Last Name")).toHaveAttribute("name", "last_name");
    expect(screen.getByLabelText("Email")).toHaveAttribute("type", "email");
    expect(screen.getByLabelText("Password")).toHaveAttribute("type", "password");
    expect(screen.getByRole("button", { name: "Register" })).toBeEnabled();
  });

  it("submits the entered values to the registration API adapter", async () => {
    const submitRegistration = vi.fn().mockResolvedValue({ username: "reviewer" });
    render(<Register submitRegistration={submitRegistration} />);
    fireEvent.change(screen.getByLabelText("Username"), { target: { value: "reviewer" } });
    fireEvent.change(screen.getByLabelText("First Name"), { target: { value: "Review" } });
    fireEvent.change(screen.getByLabelText("Last Name"), { target: { value: "Tester" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "reviewer@example.test" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "SecureExamplePassword1!" } });
    fireEvent.click(screen.getByRole("button", { name: "Register" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Account created for reviewer");
    expect(submitRegistration).toHaveBeenCalledWith({
      username: "reviewer",
      first_name: "Review",
      last_name: "Tester",
      email: "reviewer@example.test",
      password: "SecureExamplePassword1!",
    });
  });
});
