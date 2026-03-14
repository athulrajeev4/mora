"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useCreateTestSuite } from "@/lib/hooks/use-test-suites";
import { testSuitesApi } from "@/lib/api/test-suites";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import { Plus, Trash2, ArrowLeft, Sparkles, Loader2 } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

const testSuiteSchema = z.object({
  name: z.string().min(3, "Name must be at least 3 characters").max(100),
  scenario: z.string().min(10, "Scenario must be at least 10 characters"),
  prompt: z.string().min(10, "Prompt must be at least 10 characters"),
  test_cases: z.array(
    z.object({
      utterance: z.string().min(1, "Utterance is required"),
      expected_behavior: z.string().min(1, "Expected behavior is required"),
    })
  ).min(1, "At least one test case is required"),
});

type TestSuiteFormData = z.infer<typeof testSuiteSchema>;

export default function CreateTestSuitePage() {
  const router = useRouter();
  const createTestSuite = useCreateTestSuite();
  const [isGenerating, setIsGenerating] = useState(false);

  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<TestSuiteFormData>({
    resolver: zodResolver(testSuiteSchema),
    defaultValues: {
      name: "",
      scenario: "",
      prompt: "",
      test_cases: [{ utterance: "", expected_behavior: "" }],
    },
  });

  const { fields, append, remove, replace } = useFieldArray({
    control,
    name: "test_cases",
  });

  const scenario = watch("scenario");
  const prompt = watch("prompt");

  const handleGenerateWithAI = async () => {
    if (!scenario || !prompt) {
      toast.error("Please fill in both Scenario and Bot Prompt first");
      return;
    }

    setIsGenerating(true);
    try {
      const generatedCases = await testSuitesApi.generateTestCases(scenario, prompt, 5);
      replace(generatedCases);
      toast.success(`Generated ${generatedCases.length} test cases with AI! You can edit them below.`);
    } catch (error) {
      console.error("Error generating test cases:", error);
      toast.error("Failed to generate test cases. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  const onSubmit = async (data: TestSuiteFormData) => {
    try {
      const result = await createTestSuite.mutateAsync(data);
      router.push(`/test-suites/${result.id}`);
    } catch {
      // Error handled by mutation hook
    }
  };

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
        <Typography variant="h4" sx={{ fontWeight: 700 }}>Create Test Suite</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Define your test scenario and add test cases
        </Typography>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <Card className="rounded-xl">
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
            <CardDescription>Provide details about your test suite</CardDescription>
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
                placeholder="Describe the business context and what the caller is trying to achieve..."
                rows={3}
                {...register("scenario")}
                className={errors.scenario ? "border-red-500" : ""}
              />
              <Typography variant="caption" color="text.secondary">
                Example: &quot;Customer calling a restaurant to make a reservation for dinner&quot;
              </Typography>
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
                placeholder="Enter the system prompt used by the bot under test..."
                rows={4}
                {...register("prompt")}
                className={errors.prompt ? "border-red-500" : ""}
              />
              <Typography variant="caption" color="text.secondary">
                Example: &quot;You are a helpful restaurant assistant. Help customers book tables...&quot;
              </Typography>
              {errors.prompt && (
                <p className="text-sm text-red-600">{errors.prompt.message}</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-xl">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Test Cases</CardTitle>
                <CardDescription>Add test cases manually or generate them with AI</CardDescription>
              </div>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={handleGenerateWithAI}
                  disabled={isGenerating || !scenario || !prompt}
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-4 w-4" />
                      Generate with AI
                    </>
                  )}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => append({ utterance: "", expected_behavior: "" })}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Manually
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {fields.map((field, index) => (
              <div key={field.id} className="border rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <Chip label={`Test Case ${index + 1}`} size="small" variant="outlined" />
                  {fields.length > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => remove(index)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor={`test_cases.${index}.utterance`}>
                    Caller Utterance <span className="text-red-500">*</span>
                  </Label>
                  <Textarea
                    id={`test_cases.${index}.utterance`}
                    placeholder="What the caller says..."
                    rows={2}
                    {...register(`test_cases.${index}.utterance`)}
                    className={errors.test_cases?.[index]?.utterance ? "border-red-500" : ""}
                  />
                  {errors.test_cases?.[index]?.utterance && (
                    <p className="text-sm text-red-600">{errors.test_cases[index]?.utterance?.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor={`test_cases.${index}.expected_behavior`}>
                    Expected Bot Behavior <span className="text-red-500">*</span>
                  </Label>
                  <Textarea
                    id={`test_cases.${index}.expected_behavior`}
                    placeholder="What the bot should do or say..."
                    rows={2}
                    {...register(`test_cases.${index}.expected_behavior`)}
                    className={errors.test_cases?.[index]?.expected_behavior ? "border-red-500" : ""}
                  />
                  {errors.test_cases?.[index]?.expected_behavior && (
                    <p className="text-sm text-red-600">{errors.test_cases[index]?.expected_behavior?.message}</p>
                  )}
                </div>
              </div>
            ))}

            {errors.test_cases && typeof errors.test_cases.message === "string" && (
              <p className="text-sm text-red-600">{errors.test_cases.message}</p>
            )}
          </CardContent>
        </Card>

        <div className="flex gap-4">
          <Button
            type="submit"
            className="flex-1"
            disabled={isSubmitting || createTestSuite.isPending}
          >
            {isSubmitting || createTestSuite.isPending ? "Creating..." : "Create Test Suite"}
          </Button>
          <Link href="/test-suites">
            <Button type="button" variant="outline">Cancel</Button>
          </Link>
        </div>
      </form>
    </div>
  );
}
