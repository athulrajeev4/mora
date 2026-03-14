/**
 * React Query hooks for Test Suites
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { testSuitesApi } from "../api/test-suites";
import type {
  TestSuite,
  TestSuiteCreate,
  TestSuiteUpdate,
  TestCaseCreate,
  TestCaseUpdate,
} from "@/types";
import { toast } from "sonner";

// Query keys
export const testSuiteKeys = {
  all: ["test-suites"] as const,
  lists: () => [...testSuiteKeys.all, "list"] as const,
  list: () => [...testSuiteKeys.lists()] as const,
  details: () => [...testSuiteKeys.all, "detail"] as const,
  detail: (id: string) => [...testSuiteKeys.details(), id] as const,
};

// Get all test suites
export function useTestSuites() {
  return useQuery({
    queryKey: testSuiteKeys.list(),
    queryFn: testSuitesApi.getAll,
  });
}

// Get single test suite
export function useTestSuite(id: string) {
  return useQuery({
    queryKey: testSuiteKeys.detail(id),
    queryFn: () => testSuitesApi.getById(id),
    enabled: !!id,
  });
}

// Create test suite
export function useCreateTestSuite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TestSuiteCreate) => testSuitesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: testSuiteKeys.lists() });
      toast.success("Test suite created successfully");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to create test suite");
    },
  });
}

// Update test suite
export function useUpdateTestSuite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TestSuiteUpdate }) =>
      testSuitesApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: testSuiteKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: testSuiteKeys.lists() });
      toast.success("Test suite updated successfully");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to update test suite");
    },
  });
}

// Delete test suite
export function useDeleteTestSuite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => testSuitesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: testSuiteKeys.lists() });
      toast.success("Test suite deleted successfully");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to delete test suite");
    },
  });
}

// Add test case
export function useAddTestCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ suiteId, data }: { suiteId: string; data: TestCaseCreate }) =>
      testSuitesApi.addCase(suiteId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: testSuiteKeys.detail(variables.suiteId) });
      toast.success("Test case added successfully");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to add test case");
    },
  });
}

// Update test case
export function useUpdateTestCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      suiteId,
      caseId,
      data,
    }: {
      suiteId: string;
      caseId: string;
      data: TestCaseUpdate;
    }) => testSuitesApi.updateCase(suiteId, caseId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: testSuiteKeys.detail(variables.suiteId) });
      toast.success("Test case updated successfully");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to update test case");
    },
  });
}

// Delete test case
export function useDeleteTestCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ suiteId, caseId }: { suiteId: string; caseId: string }) =>
      testSuitesApi.deleteCase(suiteId, caseId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: testSuiteKeys.detail(variables.suiteId) });
      toast.success("Test case deleted successfully");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to delete test case");
    },
  });
}
