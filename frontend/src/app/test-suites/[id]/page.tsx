"use client";

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useTestSuite, useUpdateTestSuite, useDeleteTestSuite } from "@/lib/hooks/use-test-suites";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import Box from "@mui/material/Box";
import { ArrowLeft, Save, Loader2, Trash2, FileText, Edit } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";

const testSuiteSchema = z.object({
  name: z.string().min(3, "Name must be at least 3 characters").max(100),
  scenario: z.string().min(10, "Scenario must be at least 10 characters"),
  prompt: z.string().min(10, "Prompt must be at least 10 characters"),
});

type TestSuiteFormData = z.infer<typeof testSuiteSchema>;

export default function ViewTestSuitePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  
  const [isEditing, setIsEditing] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const { data: testSuite, isLoading, error } = useTestSuite(id);
  const updateTestSuite = useUpdateTestSuite();
  const deleteTestSuite = useDeleteTestSuite();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<TestSuiteFormData>({
    resolver: zodResolver(testSuiteSchema),
    values: testSuite ? {
      name: testSuite.name,
      scenario: testSuite.scenario,
      prompt: testSuite.prompt,
    } : undefined,
  });

  const onSubmit = async (data: TestSuiteFormData) => {
    try {
      await updateTestSuite.mutateAsync({
        id,
        data: {
          name: data.name,
          scenario: data.scenario,
          prompt: data.prompt,
        },
      });
      toast.success("Test suite updated successfully");
      setIsEditing(false);
    } catch {
      // Error handled by mutation hook
    }
  };

  const handleDelete = async () => {
    try {
      await deleteTestSuite.mutateAsync(id);
      router.push("/test-suites");
    } catch {
      // Error handled by mutation hook
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  if (error || !testSuite) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card className="rounded-xl">
          <CardContent className="pt-6">
            <Typography variant="body1" color="error" sx={{ textAlign: "center" }}>
              Failed to load test suite. Please try again.
            </Typography>
            <div className="mt-4 text-center">
              <Link href="/test-suites">
                <Button variant="outline">Back to Test Suites</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <Link href="/test-suites">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Test Suites
          </Button>
        </Link>
        <Box sx={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
          <div>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>{testSuite.name}</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Updated {formatDistanceToNow(new Date(testSuite.updated_at), { addSuffix: true })}
            </Typography>
          </div>
          <div className="flex gap-2">
            {!isEditing && (
              <Button onClick={() => setIsEditing(true)} size="sm">
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </Button>
            )}
            <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
              <AlertDialogTrigger asChild>
                <Button variant="destructive" size="sm">
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Test Suite?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This action cannot be undone. This will permanently delete the test suite
                    &quot;{testSuite.name}&quot; and all its test cases.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={handleDelete}
                    className="bg-red-600 hover:bg-red-700"
                  >
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </Box>
      </div>

      {isEditing ? (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <Card className="rounded-xl">
            <CardHeader>
              <CardTitle>Edit Test Suite</CardTitle>
              <CardDescription>Update test suite details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="name">
                  Test Suite Name <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="name"
                  placeholder="e.g., Restaurant Booking Bot Tests"
                  {...register("name")}
                  className={errors.name ? "border-red-500" : ""}
                />
                {errors.name && (
                  <p className="text-sm text-red-600">{errors.name.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="scenario">
                  Test Scenario <span className="text-red-500">*</span>
                </Label>
                <Textarea
                  id="scenario"
                  placeholder="Describe the business context..."
                  rows={3}
                  {...register("scenario")}
                  className={errors.scenario ? "border-red-500" : ""}
                />
                {errors.scenario && (
                  <p className="text-sm text-red-600">{errors.scenario.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="prompt">
                  Bot System Prompt <span className="text-red-500">*</span>
                </Label>
                <Textarea
                  id="prompt"
                  placeholder="Enter the system prompt..."
                  rows={4}
                  {...register("prompt")}
                  className={errors.prompt ? "border-red-500" : ""}
                />
                {errors.prompt && (
                  <p className="text-sm text-red-600">{errors.prompt.message}</p>
                )}
              </div>

              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setIsEditing(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={isSubmitting || !isDirty}>
                  {isSubmitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      Save Changes
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </form>
      ) : (
        <>
          {/* View Mode */}
          <Card className="rounded-xl">
            <CardHeader>
              <Typography variant="h6">Test Scenario</Typography>
            </CardHeader>
            <CardContent className="space-y-5">
              <div>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, display: "block", mb: 0.5 }}>
                  Scenario Description
                </Typography>
                <Typography variant="body1" sx={{ whiteSpace: "pre-wrap" }}>
                  {testSuite.scenario}
                </Typography>
              </div>
              <div>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, display: "block", mb: 0.5 }}>
                  Bot System Prompt
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    whiteSpace: "pre-wrap",
                    fontFamily: "monospace",
                    bgcolor: "grey.50",
                    p: 2,
                    borderRadius: 2,
                  }}
                >
                  {testSuite.prompt}
                </Typography>
              </div>
            </CardContent>
          </Card>

          {/* Test Cases */}
          <Card className="rounded-xl">
            <CardHeader>
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <Typography variant="h6">Test Cases</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    {testSuite.test_cases.length} test case{testSuite.test_cases.length !== 1 ? "s" : ""}
                  </Typography>
                </div>
                <Chip
                  label={`${testSuite.test_cases.length} cases`}
                  color="primary"
                  size="small"
                  variant="outlined"
                />
              </Box>
            </CardHeader>
            <CardContent>
              {testSuite.test_cases.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <Typography variant="body2" color="text.secondary">No test cases yet.</Typography>
                </div>
              ) : (
                <div className="space-y-4">
                  {testSuite.test_cases.map((testCase, index) => (
                    <div key={testCase.id} className="border rounded-xl p-5 bg-slate-50/50">
                      <div className="mb-3">
                        <Chip label={`Test Case ${index + 1}`} size="small" variant="outlined" />
                      </div>
                      <div className="space-y-3">
                        <div>
                          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                            Caller Utterance
                          </Typography>
                          <Typography variant="body2" sx={{ mt: 0.5 }}>
                            {testCase.utterance}
                          </Typography>
                        </div>
                        <div>
                          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                            Expected Bot Behavior
                          </Typography>
                          <Typography variant="body2" sx={{ mt: 0.5 }}>
                            {testCase.expected_behavior}
                          </Typography>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
