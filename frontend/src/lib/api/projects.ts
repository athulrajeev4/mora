/**
 * Project API functions
 */

import apiClient from "./client";
import type {
  Project,
  ProjectCreate,
  ProjectUpdate,
  TestRun,
} from "@/types";

export const projectsApi = {
  // Get all projects
  getAll: async (): Promise<Project[]> => {
    const { data } = await apiClient.get("/api/projects/");
    return data;
  },

  // Get single project by ID
  getById: async (id: string): Promise<Project> => {
    const { data } = await apiClient.get(`/api/projects/${id}`);
    return data;
  },

  // Create new project
  create: async (project: ProjectCreate): Promise<Project> => {
    const { data } = await apiClient.post("/api/projects/", project);
    return data;
  },

  // Update project
  update: async (id: string, project: ProjectUpdate): Promise<Project> => {
    const { data} = await apiClient.put(`/api/projects/${id}`, project);
    return data;
  },

  // Delete project
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/projects/${id}`);
  },

  // Activate project (start test execution)
  activate: async (id: string): Promise<Project> => {
    const { data } = await apiClient.post(`/api/projects/${id}/activate`);
    return data;
  },

  // Get test runs for project
  getRuns: async (id: string): Promise<TestRun[]> => {
    const { data } = await apiClient.get(`/api/projects/${id}/runs`);
    return data;
  },
};
