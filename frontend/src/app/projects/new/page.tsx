"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useCreateProject } from "@/lib/hooks/use-projects";
import { useTestSuites } from "@/lib/hooks/use-test-suites";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import { ArrowLeft, Plus, Loader2 } from "lucide-react";

const projectSchema = z.object({
  name: z.string().min(1, "Project name is required").max(100, "Name too long"),
  bot_phone_number: z
    .string()
    .min(1, "Phone number is required")
    .regex(/^\+\d{1,4}\d{6,14}$/, "Invalid phone number format. Use international format: +1234567890"),
  number_of_calls: z
    .number()
    .int("Must be a whole number")
    .min(1, "At least 1 call required")
    .max(100, "Maximum 100 calls allowed"),
  test_suite_ids: z
    .array(z.string())
    .min(1, "Select at least one test suite")
    .max(10, "Maximum 10 test suites allowed"),
});

type ProjectFormData = z.infer<typeof projectSchema>;

export default function NewProjectPage() {
  const router = useRouter();
  const { data: testSuites, isLoading: loadingTestSuites } = useTestSuites();
  const createProject = useCreateProject();
  const [selectedSuites, setSelectedSuites] = useState<Set<string>>(new Set());

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
  } = useForm<ProjectFormData>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: "",
      bot_phone_number: "",
      number_of_calls: 1,
      test_suite_ids: [],
    },
  });

  const handleSuiteToggle = (suiteId: string) => {
    const newSelected = new Set(selectedSuites);
    if (newSelected.has(suiteId)) {
      newSelected.delete(suiteId);
    } else {
      newSelected.add(suiteId);
    }
    setSelectedSuites(newSelected);
    setValue("test_suite_ids", Array.from(newSelected));
  };

  const onSubmit = async (data: ProjectFormData) => {
    await createProject.mutateAsync(data);
    router.push("/projects");
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <Link href="/projects">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Projects
          </Button>
        </Link>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>Create New Project</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Set up a new testing project with your bot phone number and test suites
        </Typography>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="space-y-6">
          <Card className="rounded-xl">
            <CardHeader>
              <CardTitle>Project Details</CardTitle>
              <CardDescription>Basic information about your project</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="name">
                  Project Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="name"
                  placeholder="e.g., Customer Support Bot - Sprint 3"
                  {...register("name")}
                  disabled={createProject.isPending}
                />
                {errors.name && (
                  <p className="text-sm text-destructive">{errors.name.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="bot_phone_number">
                  Bot Phone Number <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="bot_phone_number"
                  type="tel"
                  placeholder="+12025551234"
                  {...register("bot_phone_number")}
                  disabled={createProject.isPending}
                />
                <Typography variant="caption" color="text.secondary">
                  Use international format with country code (e.g., +1 for US)
                </Typography>
                {errors.bot_phone_number && (
                  <p className="text-sm text-destructive">{errors.bot_phone_number.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="number_of_calls">
                  Calls per Test Suite <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="number_of_calls"
                  type="number"
                  min="1"
                  max="100"
                  {...register("number_of_calls", { valueAsNumber: true })}
                  disabled={createProject.isPending}
                />
                <Typography variant="caption" color="text.secondary">
                  Number of times to execute each test case (1-100)
                </Typography>
                {errors.number_of_calls && (
                  <p className="text-sm text-destructive">{errors.number_of_calls.message}</p>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="rounded-xl">
            <CardHeader>
              <CardTitle>Select Test Suites</CardTitle>
              <CardDescription>
                Choose which test suites to include in this project (1-10 suites)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingTestSuites ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
                  <span className="ml-2 text-slate-500">Loading test suites...</span>
                </div>
              ) : !testSuites || testSuites.length === 0 ? (
                <div className="text-center py-8">
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    No test suites available
                  </Typography>
                  <Link href="/test-suites/new">
                    <Button variant="outline" size="sm">
                      <Plus className="h-4 w-4 mr-2" />
                      Create Test Suite
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="space-y-3">
                  {testSuites.map((suite) => (
                    <div
                      key={suite.id}
                      className="flex items-start space-x-3 p-4 border rounded-xl hover:bg-slate-50 transition-colors"
                    >
                      <Checkbox
                        id={suite.id}
                        checked={selectedSuites.has(suite.id)}
                        onCheckedChange={() => handleSuiteToggle(suite.id)}
                        disabled={createProject.isPending}
                      />
                      <div className="flex-1 space-y-1">
                        <label
                          htmlFor={suite.id}
                          className="text-sm font-medium leading-none cursor-pointer"
                        >
                          {suite.name}
                        </label>
                        <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
                          {suite.scenario}
                        </Typography>
                        <Chip
                          label={`${suite.test_cases?.length || 0} test case(s)`}
                          size="small"
                          variant="outlined"
                          sx={{ mt: 0.5 }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {errors.test_suite_ids && (
                <p className="text-sm text-destructive mt-2">{errors.test_suite_ids.message}</p>
              )}
              {selectedSuites.size > 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 3 }}>
                  {selectedSuites.size} suite(s) selected
                </Typography>
              )}
            </CardContent>
          </Card>

          <div className="flex justify-end gap-3">
            <Link href="/projects">
              <Button type="button" variant="outline" disabled={createProject.isPending}>
                Cancel
              </Button>
            </Link>
            <Button type="submit" disabled={createProject.isPending}>
              {createProject.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Project
                </>
              )}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
