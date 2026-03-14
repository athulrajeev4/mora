/**
 * TypeScript interfaces for Mora Platform
 */

// ============================================================================
// Test Suites
// ============================================================================

export interface TestCase {
  id: string;
  test_suite_id: string;
  utterance: string;
  expected_behavior: string;
  order: number;
  created_at: string;
}

export interface TestSuite {
  id: string;
  name: string;
  scenario: string;
  prompt: string;
  created_at: string;
  updated_at: string;
  test_cases: TestCase[];
}

export interface TestSuiteCreate {
  name: string;
  scenario: string;
  prompt: string;
  test_cases?: Array<{
    utterance: string;
    expected_behavior: string;
    order?: number;
  }>;
}

export interface TestSuiteUpdate {
  name?: string;
  scenario?: string;
  prompt?: string;
}

export interface TestCaseCreate {
  utterance: string;
  expected_behavior: string;
  order?: number;
}

export interface TestCaseUpdate {
  utterance?: string;
  expected_behavior?: string;
  order?: number;
}

// ============================================================================
// Projects
// ============================================================================

export type ProjectStatus = "pending" | "running" | "completed" | "failed";

export interface Project {
  id: string;
  name: string;
  bot_phone_number: string;
  number_of_calls: number;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
  test_suites: TestSuite[];
}

export interface ProjectCreate {
  name: string;
  bot_phone_number: string;
  number_of_calls: number;
  test_suite_ids: string[];
}

export interface ProjectUpdate {
  name?: string;
  bot_phone_number?: string;
  number_of_calls?: number;
  test_suite_ids?: string[];
}

// ============================================================================
// Test Runs
// ============================================================================

export type TestRunStatus = "pending" | "in_progress" | "success" | "failure";

export interface TestRun {
  id: string;
  project_id: string;
  test_case_id: string;
  status: TestRunStatus;
  call_sid: string | null;
  audio_url: string | null;
  transcript: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration: number | null;
  error_message: string | null;
  functional_evaluation: FunctionalEvaluation | null;
  conversational_evaluation: ConversationalEvaluation | null;
  test_case: TestCase;
}

// ============================================================================
// Evaluations
// ============================================================================

export interface FunctionalEvaluation {
  score: number;
  reasoning: string;
}

export interface ConversationalEvaluation {
  score: number;
  reasoning: string;
}

export interface EvaluationSummary {
  project_id: string;
  project_name: string;
  total_runs: number;
  evaluated_runs: number;
  successful_runs: number;
  failed_runs: number;
  pass_count: number;
  fail_count: number;
  average_functional_score: number | null;
  average_conversational_score: number | null;
  completion_percentage: number;
}

// ============================================================================
// API Responses
// ============================================================================

export interface HealthResponse {
  status: string;
  database: string;
  timestamp: string;
}

export interface ApiError {
  detail: string;
}
