/**
 * Evaluation API functions
 */

import apiClient from "./client";
import type { EvaluationSummary } from "@/types";

export const evaluationsApi = {
  // Evaluate single test run
  evaluateTestRun: async (
    testRunId: string
  ): Promise<{ message: string; test_run_id: string; status: string }> => {
    const { data } = await apiClient.post(
      `/api/evaluations/test-runs/${testRunId}/evaluate`
    );
    return data;
  },

  // Get evaluation results for test run
  getTestRunEvaluation: async (testRunId: string): Promise<any> => {
    const { data } = await apiClient.get(
      `/api/evaluations/test-runs/${testRunId}/evaluation`
    );
    return data;
  },

  // Evaluate all test runs for a project
  evaluateProject: async (
    projectId: string
  ): Promise<{
    message: string;
    project_id: string;
    test_runs_to_evaluate: number;
    status: string;
  }> => {
    const { data } = await apiClient.post(
      `/api/evaluations/projects/${projectId}/evaluate`
    );
    return data;
  },

  // Get evaluation summary for project
  getProjectSummary: async (projectId: string): Promise<EvaluationSummary> => {
    const { data } = await apiClient.get(
      `/api/evaluations/projects/${projectId}/evaluation-summary`
    );
    return data;
  },
};
