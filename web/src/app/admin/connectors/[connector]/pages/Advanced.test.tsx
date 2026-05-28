import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { Formik, Form } from "formik";
import AdvancedFormPage from "./Advanced";

function renderWithFormik(
  initialValues: Record<string, any>,
  hidePollingOptions = false
) {
  const handleSubmit = jest.fn();
  return {
    handleSubmit,
    ...render(
      <Formik initialValues={initialValues} onSubmit={handleSubmit}>
        <Form>
          <AdvancedFormPage hidePollingOptions={hidePollingOptions} />
        </Form>
      </Formik>
    ),
  };
}

describe("AdvancedFormPage - Knowledge Graph section", () => {
  const defaultValues = {
    pruneFreq: 720,
    refreshFreq: 30,
    indexingStart: "",
    kgProcessingEnabled: false,
    kgCoverageDays: undefined,
  };

  test("renders Knowledge Graph heading", () => {
    renderWithFormik(defaultValues);
    expect(screen.getByText("Knowledge Graph")).toBeInTheDocument();
  });

  test("renders the KG toggle label", () => {
    renderWithFormik(defaultValues);
    expect(
      screen.getByText("Enable Knowledge Graph Extraction")
    ).toBeInTheDocument();
  });

  test("renders the coverage days input", () => {
    renderWithFormik(defaultValues);
    expect(screen.getByText("Coverage Days")).toBeInTheDocument();
  });

  test("KG toggle is off by default", () => {
    renderWithFormik(defaultValues);
    const toggle = screen.getByRole("switch");
    expect(toggle).toHaveAttribute("aria-checked", "false");
  });

  test("KG toggle is on when kgProcessingEnabled is true", () => {
    renderWithFormik({ ...defaultValues, kgProcessingEnabled: true });
    const toggle = screen.getByRole("switch");
    expect(toggle).toHaveAttribute("aria-checked", "true");
  });

  test("clicking KG toggle changes its state", () => {
    renderWithFormik(defaultValues);
    const toggle = screen.getByRole("switch");
    expect(toggle).toHaveAttribute("aria-checked", "false");
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-checked", "true");
  });

  test("coverage days input accepts a value", () => {
    renderWithFormik({ ...defaultValues, kgCoverageDays: 90 });
    const input = screen.getByDisplayValue("90");
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute("type", "number");
  });
});

describe("AdvancedFormPage - hidePollingOptions (file connector)", () => {
  const defaultValues = {
    kgProcessingEnabled: false,
    kgCoverageDays: undefined,
  };

  test("hides prune/refresh/indexing fields when hidePollingOptions is true", () => {
    renderWithFormik(defaultValues, true);
    expect(screen.queryByText("Prune Frequency (hours)")).not.toBeInTheDocument();
    expect(screen.queryByText("Refresh Frequency (minutes)")).not.toBeInTheDocument();
    expect(screen.queryByText("Indexing Start Date")).not.toBeInTheDocument();
  });

  test("hides Reset button when hidePollingOptions is true", () => {
    renderWithFormik(defaultValues, true);
    expect(screen.queryByText("Reset")).not.toBeInTheDocument();
  });

  test("still renders KG toggle when hidePollingOptions is true", () => {
    renderWithFormik(defaultValues, true);
    expect(screen.getByText("Knowledge Graph")).toBeInTheDocument();
    expect(screen.getByRole("switch")).toBeInTheDocument();
  });

  test("hides coverage days when hidePollingOptions is true", () => {
    renderWithFormik(defaultValues, true);
    expect(screen.queryByText("Coverage Days")).not.toBeInTheDocument();
  });

  test("shows polling fields when hidePollingOptions is false", () => {
    renderWithFormik({ ...defaultValues, pruneFreq: 720, refreshFreq: 30, indexingStart: "" });
    expect(screen.getByText("Prune Frequency (hours)")).toBeInTheDocument();
    expect(screen.getByText("Refresh Frequency (minutes)")).toBeInTheDocument();
  });
});
