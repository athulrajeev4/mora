"use client";

import Link from "next/link";
import { useTestSuites, useDeleteTestSuite } from "@/lib/hooks/use-test-suites";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import Box from "@mui/material/Box";
import { Plus, Edit, Trash2, FlaskConical } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import type { TestSuite } from "@/types";

export default function TestSuitesPage() {
  const { data: testSuites, isLoading, error } = useTestSuites();
  const deleteTestSuite = useDeleteTestSuite();

  const handleDelete = (id: string) => {
    deleteTestSuite.mutate(id);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-64 bg-slate-100 animate-pulse rounded" />
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 bg-slate-100 animate-pulse rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 rounded-xl">
        <CardHeader>
          <CardTitle className="text-red-600">Error Loading Test Suites</CardTitle>
          <CardDescription>
            Failed to load test suites. Please check your backend connection.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Box sx={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Test Suites</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Manage test scenarios and cases for your voice agents
          </Typography>
        </div>
        <Link href="/test-suites/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Test Suite
          </Button>
        </Link>
      </Box>

      {/* Empty State */}
      {testSuites?.length === 0 && (
        <Card className="border-dashed rounded-xl">
          <CardHeader className="text-center py-12">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-50">
              <FlaskConical className="h-8 w-8 text-indigo-600" />
            </div>
            <CardTitle>No test suites yet</CardTitle>
            <CardDescription className="mt-2">
              Get started by creating your first test suite
            </CardDescription>
            <div className="mt-6">
              <Link href="/test-suites/new">
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Test Suite
                </Button>
              </Link>
            </div>
          </CardHeader>
        </Card>
      )}

      {/* Test Suites Grid */}
      {testSuites && testSuites.length > 0 && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {testSuites.map((suite) => (
            <TestSuiteCard
              key={suite.id}
              suite={suite}
              onDelete={handleDelete}
              isDeleting={deleteTestSuite.isPending}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function TestSuiteCard({
  suite,
  onDelete,
  isDeleting,
}: {
  suite: TestSuite;
  onDelete: (id: string) => void;
  isDeleting: boolean;
}) {
  return (
    <Card className="hover:shadow-md transition-shadow rounded-xl border">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <Typography variant="h6" noWrap>{suite.name}</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
              {suite.scenario}
            </Typography>
          </div>
          <Chip
            label={`${suite.test_cases.length} ${suite.test_cases.length === 1 ? "case" : "cases"}`}
            size="small"
            color="primary"
            variant="outlined"
            sx={{ ml: 1.5 }}
          />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <Typography variant="caption" color="text.secondary">
            Updated {formatDistanceToNow(new Date(suite.updated_at), { addSuffix: true })}
          </Typography>

          <div className="flex gap-2">
            <Link href={`/test-suites/${suite.id}`} className="flex-1">
              <Button variant="outline" className="w-full">
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </Button>
            </Link>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  className="text-red-600 hover:bg-red-50 hover:text-red-700"
                  disabled={isDeleting}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Test Suite?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will permanently delete &quot;{suite.name}&quot; and all its test cases.
                    This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => onDelete(suite.id)}
                    className="bg-red-600 hover:bg-red-700"
                  >
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
