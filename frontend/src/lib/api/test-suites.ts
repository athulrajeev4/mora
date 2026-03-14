/**
 * Test Suite API functions
 */

import apiClient from "./client";
import type {
  TestSuite,
  TestSuiteCreate,
  TestSuiteUpdate,
  TestCase,
  TestCaseCreate,
  TestCaseUpdate,
} from "@/types";

export const testSuitesApi = {
  // Get all test suites
  getAll: async (): Promise<TestSuite[]> => {
    const { data } = await apiClient.get("/api/test-suites/");
    return data;
  },

  // Get single test suite by ID
  getById: async (id: string): Promise<TestSuite> => {
    const { data } = await apiClient.get(`/api/test-suites/${id}`);
    return data;
  },

  // Create new test suite
  create: async (testSuite: TestSuiteCreate): Promise<TestSuite> => {
    const { data } = await apiClient.post("/api/test-suites/", testSuite);
    return data;
  },

  // Update test suite
  update: async (
    id: string,
    testSuite: TestSuiteUpdate
  ): Promise<TestSuite> => {
    const { data } = await apiClient.put(`/api/test-suites/${id}`, testSuite);
    return data;
  },

  // Delete test suite
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/test-suites/${id}`);
  },

  // Add test case to suite
  addCase: async (suiteId: string, testCase: TestCaseCreate): Promise<TestCase> => {
    const { data } = await apiClient.post(
      `/api/test-suites/${suiteId}/cases`,
      testCase
    );
    return data;
  },

  // Update test case
  updateCase: async (
    suiteId: string,
    caseId: string,
    testCase: TestCaseUpdate
  ): Promise<TestCase> => {
    const { data } = await apiClient.put(
      `/api/test-suites/${suiteId}/cases/${caseId}`,
      testCase
    );
    return data;
  },

  // Delete test case
  deleteCase: async (suiteId: string, caseId: string): Promise<void> => {
    await apiClient.delete(`/api/test-suites/${suiteId}/cases/${caseId}`);
  },

  // Generate test cases using AI
  generateTestCases: async (
    scenario: string,
    prompt: string,
    numCases: number = 5
  ): Promise<Array<{ utterance: string; expected_behavior: string }>> => {
    const { data } = await apiClient.post("/api/test-suites/generate-test-cases", {
      scenario,
      prompt,
      num_cases: numCases,
    });
    return data;
  },
};
