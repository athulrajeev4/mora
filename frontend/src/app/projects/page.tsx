"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useProjects, useDeleteProject } from "@/lib/hooks/use-projects";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
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
import { Plus, Trash2, Play, CheckCircle2, XCircle, Clock, Loader2 } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import type { Project } from "@/types";

export default function ProjectsPage() {
  const router = useRouter();
  const { data: projects, isLoading, error } = useProjects();
  const deleteProject = useDeleteProject();
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const handleDelete = async () => {
    if (!deleteId) return;
    await deleteProject.mutateAsync(deleteId);
    setDeleteId(null);
  };

  if (isLoading) {
    return (
      <div>
        <Box sx={{ mb: 5 }}>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Projects</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Manage your testing projects and trigger test executions
          </Typography>
        </Box>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse rounded-xl">
              <CardHeader>
                <div className="h-6 bg-slate-100 rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-slate-100 rounded w-1/2"></div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="h-4 bg-slate-100 rounded"></div>
                  <div className="h-4 bg-slate-100 rounded"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive rounded-xl">
        <CardHeader>
          <CardTitle className="text-destructive">Error Loading Projects</CardTitle>
          <CardDescription>
            {error instanceof Error ? error.message : "Failed to load projects"}
          </CardDescription>
        </CardHeader>
        <CardFooter>
          <Button onClick={() => window.location.reload()}>Retry</Button>
        </CardFooter>
      </Card>
    );
  }

  const getStatusChip = (status: Project["status"]) => {
    const config: Record<string, { color: "default" | "primary" | "success" | "error" | "warning"; label: string }> = {
      pending: { color: "default", label: "Pending" },
      running: { color: "primary", label: "Running" },
      completed: { color: "success", label: "Completed" },
      failed: { color: "error", label: "Failed" },
    };
    const c = config[status] || config.pending;
    return (
      <Chip
        label={c.label}
        color={c.color}
        size="small"
        variant="outlined"
        icon={
          status === "running" ? <Loader2 size={14} className="animate-spin" /> :
          status === "completed" ? <CheckCircle2 size={14} /> :
          status === "failed" ? <XCircle size={14} /> :
          <Clock size={14} />
        }
      />
    );
  };

  return (
    <div>
      {/* Header */}
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", mb: 5 }}>
        <div>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Projects</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Manage your testing projects and trigger test executions
          </Typography>
        </div>
        <Link href="/projects/new">
          <Button size="lg">
            <Plus className="h-4 w-4 mr-2" />
            New Project
          </Button>
        </Link>
      </Box>

      {/* Empty State */}
      {!projects || projects.length === 0 ? (
        <Card className="text-center py-12 rounded-xl">
          <CardHeader>
            <CardTitle>No Projects Yet</CardTitle>
            <CardDescription>
              Create your first project to start running automated voice tests
            </CardDescription>
          </CardHeader>
          <CardFooter className="justify-center">
            <Link href="/projects/new">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Create Project
              </Button>
            </Link>
          </CardFooter>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Card key={project.id} className="flex flex-col hover:shadow-md transition-shadow rounded-xl border">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <Typography variant="h6" noWrap>{project.name}</Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: "block" }}>
                      {project.test_suites?.length || 0} test suite(s) attached
                    </Typography>
                  </div>
                  {getStatusChip(project.status)}
                </div>
              </CardHeader>
              
              <CardContent className="flex-1 pt-0">
                <div className="space-y-2.5 text-sm">
                  <div className="flex justify-between">
                    <Typography variant="body2" color="text.secondary">Bot Phone:</Typography>
                    <Typography variant="body2" sx={{ fontFamily: "monospace", fontWeight: 500 }}>{project.bot_phone_number}</Typography>
                  </div>
                  <div className="flex justify-between">
                    <Typography variant="body2" color="text.secondary">Test Suites:</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{project.test_suites?.length || 0}</Typography>
                  </div>
                  <div className="flex justify-between">
                    <Typography variant="body2" color="text.secondary">Calls per Suite:</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{project.number_of_calls}</Typography>
                  </div>
                  {project.updated_at && (
                    <Typography variant="caption" color="text.secondary" sx={{ display: "block", pt: 1.5, borderTop: "1px solid", borderColor: "divider" }}>
                      Updated {formatDistanceToNow(new Date(project.updated_at), { addSuffix: true })}
                    </Typography>
                  )}
                </div>
              </CardContent>

              <CardFooter className="flex gap-2 pt-4 border-t">
                <Button
                  variant="default"
                  size="sm"
                  className="flex-1"
                  onClick={() => router.push(`/projects/${project.id}`)}
                >
                  <Play className="h-3 w-3 mr-1" />
                  View Details
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setDeleteId(project.id)}
                  disabled={deleteProject.isPending}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
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
