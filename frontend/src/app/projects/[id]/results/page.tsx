"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useProject, useProjectRuns } from "@/lib/hooks/use-projects";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import LinearProgress from "@mui/material/LinearProgress";
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  TrendingUp,
  TrendingDown,
  Loader2,
  PlayCircle,
  MessageSquare,
  Clock,
  Phone,
  RefreshCw,
} from "lucide-react";
import type { TestRun } from "@/types";
import { evaluationsApi } from "@/lib/api/evaluations";
import { toast } from "sonner";

function getFunctionalScore(run: TestRun): number {
  return run.functional_evaluation?.score ?? 0;
}

function getConversationalScore(run: TestRun): number {
  return run.conversational_evaluation?.overall_score ?? 0;
}

function getConversationalReasoning(run: TestRun): string {
  const eval_ = run.conversational_evaluation;
  if (!eval_) return "";
  return eval_.feedback || "";
}

const PASS_THRESHOLD = 70;

export default function ProjectResultsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: project, isLoading: loadingProject } = useProject(id);
  const { data: runs, isLoading: loadingRuns, refetch } = useProjectRuns(id);
  const [selectedRun, setSelectedRun] = useState<TestRun | null>(null);
  const [evaluating, setEvaluating] = useState(false);

  const evaluatedRuns = runs?.filter((r) => r.functional_evaluation && r.conversational_evaluation) || [];
  
  const totalRuns = runs?.length || 0;
  const completedRuns = runs?.filter((r) => r.status === "success").length || 0;
  const passedRuns = evaluatedRuns.filter((r) => getFunctionalScore(r) >= PASS_THRESHOLD).length;
  const passRate = evaluatedRuns.length > 0 ? (passedRuns / evaluatedRuns.length) * 100 : 0;
  
  const avgFunctionalScore = evaluatedRuns.length > 0
    ? evaluatedRuns.reduce((sum, r) => sum + getFunctionalScore(r), 0) / evaluatedRuns.length
    : 0;
    
  const avgConversationalScore = evaluatedRuns.length > 0
    ? evaluatedRuns.reduce((sum, r) => sum + getConversationalScore(r), 0) / evaluatedRuns.length
    : 0;

  const hasUnevaluatedRuns = runs?.some(
    (r) => r.status === "success" && (!r.functional_evaluation || !r.conversational_evaluation)
  );

  const handleEvaluate = async () => {
    setEvaluating(true);
    try {
      await evaluationsApi.evaluateProject(id);
      toast.success("Evaluation started — results will appear shortly");
      setTimeout(() => refetch(), 5000);
      setTimeout(() => refetch(), 15000);
      setTimeout(() => refetch(), 30000);
    } catch {
      toast.error("Failed to trigger evaluation");
    } finally {
      setEvaluating(false);
    }
  };

  if (loadingProject || loadingRuns) {
    return (
      <div className="flex justify-center items-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!project || !runs) {
    return (
      <Card className="border-destructive rounded-xl">
        <CardHeader>
          <CardTitle className="text-destructive">No Results Found</CardTitle>
          <CardDescription>Unable to load project results</CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/projects">
            <Button>Back to Projects</Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <Link href={`/projects/${id}`}>
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Project
          </Button>
        </Link>
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 2 }}>
          <div>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              {project.name} — Results
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Comprehensive analysis of test execution and evaluation results
            </Typography>
          </div>
          <Box sx={{ display: "flex", gap: 1.5 }}>
            {hasUnevaluatedRuns && (
              <Button onClick={handleEvaluate} disabled={evaluating}>
                {evaluating ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <PlayCircle className="h-4 w-4 mr-2" />
                )}
                Run Evaluation
              </Button>
            )}
            <Button variant="outline" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </Box>
        </Box>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-5 md:grid-cols-4 mb-8">
        <Paper sx={{ p: 3, borderRadius: 2.5, border: "1px solid", borderColor: "divider" }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, display: "block", mb: 1 }}>
            Pass Rate
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1.5 }}>
            <Typography variant="h4" sx={{ fontWeight: 800 }}>
              {passRate.toFixed(0)}%
            </Typography>
            {passRate >= 70 ? (
              <TrendingUp className="h-5 w-5 text-emerald-500" />
            ) : (
              <TrendingDown className="h-5 w-5 text-red-500" />
            )}
          </Box>
          <LinearProgress
            variant="determinate"
            value={passRate}
            color={passRate >= 70 ? "success" : "error"}
            sx={{ borderRadius: 2, height: 6 }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
            {passedRuns} of {evaluatedRuns.length} passed (≥{PASS_THRESHOLD})
          </Typography>
        </Paper>

        <Paper sx={{ p: 3, borderRadius: 2.5, border: "1px solid", borderColor: "divider" }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, display: "block", mb: 1 }}>
            Functional Score
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1.5 }}>
            <Typography variant="h4" sx={{ fontWeight: 800 }}>
              {avgFunctionalScore.toFixed(0)}
            </Typography>
            <CheckCircle2 className="h-5 w-5 text-indigo-500" />
          </Box>
          <LinearProgress
            variant="determinate"
            value={avgFunctionalScore}
            color="primary"
            sx={{ borderRadius: 2, height: 6 }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
            Average out of 100
          </Typography>
        </Paper>

        <Paper sx={{ p: 3, borderRadius: 2.5, border: "1px solid", borderColor: "divider" }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, display: "block", mb: 1 }}>
            Conversational Score
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1.5 }}>
            <Typography variant="h4" sx={{ fontWeight: 800 }}>
              {avgConversationalScore.toFixed(0)}
            </Typography>
            <MessageSquare className="h-5 w-5 text-violet-500" />
          </Box>
          <LinearProgress
            variant="determinate"
            value={avgConversationalScore}
            color="secondary"
            sx={{ borderRadius: 2, height: 6 }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
            Average out of 100
          </Typography>
        </Paper>

        <Paper sx={{ p: 3, borderRadius: 2.5, border: "1px solid", borderColor: "divider" }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, display: "block", mb: 1 }}>
            Completion Rate
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1.5 }}>
            <Typography variant="h4" sx={{ fontWeight: 800 }}>
              {totalRuns > 0 ? ((completedRuns / totalRuns) * 100).toFixed(0) : 0}%
            </Typography>
            <Clock className="h-5 w-5 text-amber-500" />
          </Box>
          <LinearProgress
            variant="determinate"
            value={totalRuns > 0 ? (completedRuns / totalRuns) * 100 : 0}
            color="warning"
            sx={{ borderRadius: 2, height: 6 }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
            {completedRuns} of {totalRuns} completed
          </Typography>
        </Paper>
      </div>

      {/* Unevaluated notice */}
      {evaluatedRuns.length === 0 && completedRuns > 0 && (
        <Paper sx={{ p: 3, mb: 4, borderRadius: 2.5, border: "1px solid", borderColor: "warning.light", bgcolor: "warning.50" }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <Loader2 className="h-5 w-5 text-amber-500" />
            <div>
              <Typography variant="body1" sx={{ fontWeight: 600 }}>
                Evaluation Pending
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {completedRuns} test run(s) completed but not yet evaluated. Click &quot;Run Evaluation&quot; to analyze results with AI.
              </Typography>
            </div>
          </Box>
        </Paper>
      )}

      {/* Test Runs Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Runs List */}
        <div className="space-y-4">
          <Typography variant="h6">Test Runs</Typography>
          {runs.length === 0 ? (
            <Card className="rounded-xl">
              <CardContent className="py-8 text-center">
                <Typography variant="body2" color="text.secondary">No test runs yet</Typography>
              </CardContent>
            </Card>
          ) : (
            runs.map((run) => (
              <Card
                key={run.id}
                className={`cursor-pointer transition-all hover:shadow-md rounded-xl border ${
                  selectedRun?.id === run.id ? "ring-2 ring-indigo-500" : ""
                }`}
                onClick={() => setSelectedRun(run)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <Typography variant="body1" sx={{ fontWeight: 500 }} noWrap>
                        {run.test_case?.utterance || "Test Run"}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontFamily: "monospace" }}>
                        {run.call_sid || "No Call SID"}
                      </Typography>
                    </div>
                    <Chip
                      label={run.status}
                      color={
                        run.status === "success" ? "success" :
                        run.status === "failure" ? "error" : "default"
                      }
                      size="small"
                      variant="outlined"
                    />
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex gap-4 text-sm">
                    {run.functional_evaluation && (
                      <div className="flex items-center gap-1.5">
                        {getFunctionalScore(run) >= PASS_THRESHOLD ? (
                          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-500" />
                        )}
                        <Typography variant="body2">
                          Functional: {getFunctionalScore(run)}/100
                        </Typography>
                      </div>
                    )}
                    {run.conversational_evaluation && (
                      <div className="flex items-center gap-1.5">
                        <MessageSquare className="h-4 w-4 text-violet-500" />
                        <Typography variant="body2">
                          Conv: {getConversationalScore(run)}/100
                        </Typography>
                      </div>
                    )}
                    {!run.functional_evaluation && !run.conversational_evaluation && run.status === "success" && (
                      <Typography variant="caption" color="text.secondary">
                        Awaiting evaluation...
                      </Typography>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Selected Run Details */}
        <div className="lg:sticky lg:top-8 h-fit">
          {!selectedRun ? (
            <Card className="rounded-xl">
              <CardContent className="py-12 text-center">
                <PlayCircle className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                <Typography variant="body2" color="text.secondary">
                  Select a test run to view detailed results
                </Typography>
              </CardContent>
            </Card>
          ) : (
            <Card className="rounded-xl">
              <CardHeader>
                <Typography variant="h6">Test Run Details</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500, mt: 0.5 }}>
                  {selectedRun.test_case?.utterance || "Test Run"}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ fontFamily: "monospace" }}>
                  {selectedRun.call_sid}
                </Typography>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="functional" className="w-full">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="functional">Functional</TabsTrigger>
                    <TabsTrigger value="conversational">Conversational</TabsTrigger>
                    <TabsTrigger value="transcript">Transcript</TabsTrigger>
                  </TabsList>

                  <TabsContent value="functional" className="space-y-4 mt-4">
                    {selectedRun.functional_evaluation ? (
                      <>
                        <div className="flex items-center justify-between p-4 border rounded-xl">
                          <div className="flex items-center gap-2">
                            {getFunctionalScore(selectedRun) >= PASS_THRESHOLD ? (
                              <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                            ) : (
                              <XCircle className="h-5 w-5 text-red-500" />
                            )}
                            <Typography variant="body1" sx={{ fontWeight: 600 }}>
                              {selectedRun.functional_evaluation.passed ? "PASSED" : "FAILED"}
                            </Typography>
                          </div>
                          <Chip
                            label={`${getFunctionalScore(selectedRun)}/100`}
                            color={getFunctionalScore(selectedRun) >= PASS_THRESHOLD ? "success" : "error"}
                            variant="outlined"
                          />
                        </div>
                        <div>
                          <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>Score</Typography>
                          <LinearProgress
                            variant="determinate"
                            value={getFunctionalScore(selectedRun)}
                            color={getFunctionalScore(selectedRun) >= PASS_THRESHOLD ? "success" : "error"}
                            sx={{ borderRadius: 2, height: 8, mb: 2 }}
                          />
                        </div>
                        <div>
                          <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>Reasoning</Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ p: 2, bgcolor: "grey.50", borderRadius: 2 }}>
                            {selectedRun.functional_evaluation.reasoning}
                          </Typography>
                        </div>
                        {selectedRun.functional_evaluation.matched_behaviors && selectedRun.functional_evaluation.matched_behaviors.length > 0 && (
                          <div>
                            <Typography variant="body2" sx={{ fontWeight: 600, mb: 1, color: "success.main" }}>
                              Matched Behaviors
                            </Typography>
                            <ul className="list-disc list-inside space-y-1">
                              {selectedRun.functional_evaluation.matched_behaviors.map((b, i) => (
                                <li key={i}>
                                  <Typography variant="body2" component="span" color="text.secondary">{b}</Typography>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {selectedRun.functional_evaluation.missing_behaviors && selectedRun.functional_evaluation.missing_behaviors.length > 0 && (
                          <div>
                            <Typography variant="body2" sx={{ fontWeight: 600, mb: 1, color: "error.main" }}>
                              Missing Behaviors
                            </Typography>
                            <ul className="list-disc list-inside space-y-1">
                              {selectedRun.functional_evaluation.missing_behaviors.map((b, i) => (
                                <li key={i}>
                                  <Typography variant="body2" component="span" color="text.secondary">{b}</Typography>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </>
                    ) : (
                      <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", py: 8 }}>
                        No functional evaluation available
                      </Typography>
                    )}
                  </TabsContent>

                  <TabsContent value="conversational" className="space-y-4 mt-4">
                    {selectedRun.conversational_evaluation ? (
                      <>
                        <div className="p-4 border rounded-xl">
                          <div className="flex items-center justify-between mb-3">
                            <Typography variant="body1" sx={{ fontWeight: 600 }}>Overall Score</Typography>
                            <Chip
                              label={`${getConversationalScore(selectedRun)}/100`}
                              color={getConversationalScore(selectedRun) >= PASS_THRESHOLD ? "success" : "error"}
                              variant="outlined"
                            />
                          </div>
                          <LinearProgress
                            variant="determinate"
                            value={getConversationalScore(selectedRun)}
                            color={getConversationalScore(selectedRun) >= PASS_THRESHOLD ? "success" : "error"}
                            sx={{ borderRadius: 2, height: 8 }}
                          />
                        </div>

                        {/* Sub-scores */}
                        <div className="grid grid-cols-2 gap-3">
                          {(["fluency", "naturalness", "error_handling", "coherence"] as const).map((key) => {
                            const val = selectedRun.conversational_evaluation?.[key];
                            if (val == null) return null;
                            const label = key.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
                            return (
                              <Paper key={key} sx={{ p: 2, borderRadius: 2, border: "1px solid", borderColor: "divider" }}>
                                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                                  {label}
                                </Typography>
                                <Typography variant="h6" sx={{ fontWeight: 700 }}>{val}</Typography>
                                <LinearProgress
                                  variant="determinate"
                                  value={val}
                                  sx={{ borderRadius: 2, height: 4, mt: 0.5 }}
                                />
                              </Paper>
                            );
                          })}
                        </div>

                        <div>
                          <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>Feedback</Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ p: 2, bgcolor: "grey.50", borderRadius: 2 }}>
                            {getConversationalReasoning(selectedRun)}
                          </Typography>
                        </div>

                        {selectedRun.conversational_evaluation.strengths && selectedRun.conversational_evaluation.strengths.length > 0 && (
                          <div>
                            <Typography variant="body2" sx={{ fontWeight: 600, mb: 1, color: "success.main" }}>
                              Strengths
                            </Typography>
                            <ul className="list-disc list-inside space-y-1">
                              {selectedRun.conversational_evaluation.strengths.map((s, i) => (
                                <li key={i}>
                                  <Typography variant="body2" component="span" color="text.secondary">{s}</Typography>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {selectedRun.conversational_evaluation.weaknesses && selectedRun.conversational_evaluation.weaknesses.length > 0 && (
                          <div>
                            <Typography variant="body2" sx={{ fontWeight: 600, mb: 1, color: "error.main" }}>
                              Areas for Improvement
                            </Typography>
                            <ul className="list-disc list-inside space-y-1">
                              {selectedRun.conversational_evaluation.weaknesses.map((w, i) => (
                                <li key={i}>
                                  <Typography variant="body2" component="span" color="text.secondary">{w}</Typography>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </>
                    ) : (
                      <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", py: 8 }}>
                        No conversational evaluation available
                      </Typography>
                    )}
                  </TabsContent>

                  <TabsContent value="transcript" className="space-y-4 mt-4">
                    {selectedRun.transcript ? (
                      <div className="space-y-3 max-h-[600px] overflow-y-auto">
                        {selectedRun.transcript.split("\n").filter(Boolean).map((line, idx) => {
                          const isCaller = line.toLowerCase().startsWith("caller:");
                          const isBot = line.toLowerCase().startsWith("bot:");
                          
                          return (
                            <div
                              key={idx}
                              className={`p-3 rounded-xl text-sm ${
                                isCaller
                                  ? "bg-indigo-50 border-l-4 border-indigo-500"
                                  : isBot
                                  ? "bg-violet-50 border-l-4 border-violet-500"
                                  : "bg-slate-50"
                              }`}
                            >
                              {line}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", py: 8 }}>
                        No transcript available
                      </Typography>
                    )}
                    
                    {selectedRun.audio_url && (
                      <div className="pt-4 border-t">
                        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                          <Phone className="h-4 w-4" />
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>Call Recording</Typography>
                        </Box>
                        <audio controls className="w-full">
                          <source src={selectedRun.audio_url} type="audio/mpeg" />
                          Your browser does not support the audio element.
                        </audio>
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
