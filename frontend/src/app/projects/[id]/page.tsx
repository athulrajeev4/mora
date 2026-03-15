"use client";

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useProject, useProjectRuns, useActivateProject, useDeleteProject } from "@/lib/hooks/use-projects";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import {
  ArrowLeft,
  Play,
  Trash2,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  Phone,
  FileText,
  BarChart3,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import type { TestRun } from "@/types";

export default function ProjectDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const { data: project, isLoading: loadingProject, error } = useProject(id);
  const { data: runs, isLoading: loadingRuns } = useProjectRuns(id);
  const activateProject = useActivateProject();
  const deleteProject = useDeleteProject();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const handleActivate = async () => {
    await activateProject.mutateAsync(id);
  };

  const handleDelete = async () => {
    await deleteProject.mutateAsync(id);
    router.push("/projects");
  };

  const getRunStatusChip = (status: TestRun["status"]) => {
    const config: Record<string, { color: "default" | "primary" | "success" | "error"; label: string }> = {
      pending: { color: "default", label: "Pending" },
      in_progress: { color: "primary", label: "Running" },
      success: { color: "success", label: "Success" },
      failure: { color: "error", label: "Failed" },
    };
    const c = config[status] || config.pending;
    return <Chip label={c.label} color={c.color} size="small" variant="outlined" />;
  };

  const getProjectStatusChip = (status: "pending" | "running" | "completed" | "failed") => {
    const config: Record<string, { color: "default" | "primary" | "success" | "error"; label: string }> = {
      pending: { color: "default", label: "Pending" },
      running: { color: "primary", label: "Running" },
      completed: { color: "success", label: "Completed" },
      failed: { color: "error", label: "Failed" },
    };
    const c = config[status];
    return <Chip label={c.label} color={c.color} size="small" variant="outlined" />;
  };

  if (loadingProject) {
    return (
      <Card className="rounded-xl">
        <CardHeader className="animate-pulse">
          <div className="h-8 bg-slate-100 rounded w-1/3 mb-2"></div>
          <div className="h-4 bg-slate-100 rounded w-1/4"></div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="h-4 bg-slate-100 rounded w-full"></div>
            <div className="h-4 bg-slate-100 rounded w-3/4"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !project) {
    return (
      <Card className="border-destructive rounded-xl">
        <CardHeader>
          <CardTitle className="text-destructive">Error Loading Project</CardTitle>
          <CardDescription>
            {error instanceof Error ? error.message : "Project not found"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/projects">
            <Button>Back to Projects</Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  const canActivate = project.status === "pending" || project.status === "failed";
  const isRunning = project.status === "running";

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <Link href="/projects">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Projects
          </Button>
        </Link>
        <Box sx={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
          <div>
            <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1 }}>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>{project.name}</Typography>
              {getProjectStatusChip(project.status)}
            </Box>
            <Typography variant="body2" color="text.secondary">
              Created {formatDistanceToNow(new Date(project.created_at), { addSuffix: true })}
            </Typography>
          </div>
          <div className="flex gap-2">
            {runs && runs.length > 0 && (
              <Link href={`/projects/${id}/results`}>
                <Button variant="outline" size="lg">
                  <BarChart3 className="h-4 w-4 mr-2" />
                  View Results
                </Button>
              </Link>
            )}
            <Button
              size="lg"
              onClick={handleActivate}
              disabled={!canActivate || activateProject.isPending}
            >
              {activateProject.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Activating...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  {isRunning ? "Running" : "Activate Project"}
                </>
              )}
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={() => setShowDeleteDialog(true)}
              disabled={deleteProject.isPending || isRunning}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </Box>
      </div>

      {/* Stat Cards */}
      <div className="grid gap-5 md:grid-cols-3 mb-6">
        <Paper sx={{ p: 3, borderRadius: 2.5, border: "1px solid", borderColor: "divider" }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
            <Phone size={16} className="text-slate-400" />
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
              Bot Phone Number
            </Typography>
          </Box>
          <Typography variant="h5" sx={{ fontFamily: "monospace", fontWeight: 700 }}>
            {project.bot_phone_number}
          </Typography>
        </Paper>

        <Paper sx={{ p: 3, borderRadius: 2.5, border: "1px solid", borderColor: "divider" }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
            <FileText size={16} className="text-slate-400" />
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
              Test Suites
            </Typography>
          </Box>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            {project.test_suites?.length || 0}
          </Typography>
          <Typography variant="caption" color="text.secondary">suites attached</Typography>
        </Paper>

        <Paper sx={{ p: 3, borderRadius: 2.5, border: "1px solid", borderColor: "divider" }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
            <BarChart3 size={16} className="text-slate-400" />
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
              Calls per Suite
            </Typography>
          </Box>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            {project.number_of_calls}
          </Typography>
          <Typography variant="caption" color="text.secondary">executions each</Typography>
        </Paper>
      </div>

      {/* Test Suites List */}
      <Card className="mb-6 rounded-xl">
        <CardHeader>
          <Typography variant="h6">Attached Test Suites</Typography>
          <Typography variant="body2" color="text.secondary">
            Test suites included in this project
          </Typography>
        </CardHeader>
        <CardContent>
          {!project.test_suites || project.test_suites.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", py: 4 }}>
              No test suites attached
            </Typography>
          ) : (
            <div className="space-y-3">
              {project.test_suites.map((suite) => (
                <div key={suite.id} className="flex items-center justify-between p-4 border rounded-xl">
                  <div>
                    <Typography variant="body1" sx={{ fontWeight: 500 }}>{suite.name}</Typography>
                    <Chip
                      label={`${suite.test_cases?.length || 0} test case(s)`}
                      size="small"
                      variant="outlined"
                      sx={{ mt: 0.5 }}
                    />
                  </div>
                  <Link href={`/test-suites/${suite.id}`}>
                    <Button variant="outline" size="sm">View Suite</Button>
                  </Link>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Test Runs Table */}
      <Card className="rounded-xl">
        <CardHeader>
          <Typography variant="h6">Test Runs</Typography>
          <div>
            {isRunning && (
              <span className="flex items-center gap-2 text-sm text-indigo-600">
                <Loader2 className="h-3 w-3 animate-spin" />
                Test execution in progress...
              </span>
            )}
            {!isRunning && runs && runs.length > 0 && (
              <Typography variant="body2" color="text.secondary">{runs.length} test run(s)</Typography>
            )}
            {!isRunning && (!runs || runs.length === 0) && (
              <Typography variant="body2" color="text.secondary">No test runs yet</Typography>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {loadingRuns ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
            </div>
          ) : !runs || runs.length === 0 ? (
            <div className="text-center py-8">
              <Typography variant="body2" color="text.secondary">
                No test runs yet. Activate the project to start testing.
              </Typography>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Test Case</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Call SID</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead>Functional</TableHead>
                    <TableHead>Conversational</TableHead>
                    <TableHead>Started</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runs.map((run) => {
                    const funcScore = run.functional_evaluation?.score ?? null;
                    const convScore = run.conversational_evaluation?.overall_score ?? null;
                    return (
                      <TableRow key={run.id} className="cursor-pointer hover:bg-slate-50">
                        <TableCell className="font-medium max-w-xs truncate">
                          {run.test_case?.utterance || "Test Run"}
                        </TableCell>
                        <TableCell>{getRunStatusChip(run.status)}</TableCell>
                        <TableCell className="font-mono text-xs">
                          {run.call_sid ? run.call_sid.substring(0, 12) + "..." : "\u2014"}
                        </TableCell>
                        <TableCell>
                          {run.started_at && run.completed_at
                            ? `${Math.round((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000)}s`
                            : "\u2014"}
                        </TableCell>
                        <TableCell>
                          {funcScore != null ? (
                            <Chip
                              label={`${funcScore}/100`}
                              color={funcScore >= 70 ? "success" : "error"}
                              size="small"
                              variant="outlined"
                            />
                          ) : "\u2014"}
                        </TableCell>
                        <TableCell>
                          {convScore != null ? (
                            <Chip
                              label={`${convScore}/100`}
                              color={convScore >= 70 ? "success" : "error"}
                              size="small"
                              variant="outlined"
                            />
                          ) : "\u2014"}
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption" color="text.secondary">
                            {run.started_at
                              ? formatDistanceToNow(new Date(run.started_at), { addSuffix: true })
                              : "\u2014"}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Project?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the project
              and all associated test runs and evaluations.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
