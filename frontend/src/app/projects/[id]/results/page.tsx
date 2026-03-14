"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useProject, useProjectRuns } from "@/lib/hooks/use-projects";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
} from "lucide-react";
import type { TestRun } from "@/types";

export default function ProjectResultsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: project, isLoading: loadingProject } = useProject(id);
  const { data: runs, isLoading: loadingRuns } = useProjectRuns(id);
  const [selectedRun, setSelectedRun] = useState<TestRun | null>(null);

  const evaluatedRuns = runs?.filter((r) => r.functional_evaluation && r.conversational_evaluation) || [];
  
  const totalRuns = runs?.length || 0;
  const completedRuns = runs?.filter((r) => r.status === "success").length || 0;
  const passedRuns = evaluatedRuns.filter((r) => (r.functional_evaluation?.score || 0) >= 7).length;
  const passRate = evaluatedRuns.length > 0 ? (passedRuns / evaluatedRuns.length) * 100 : 0;
  
  const avgFunctionalScore = evaluatedRuns.length > 0
    ? evaluatedRuns.reduce((sum, r) => sum + (r.functional_evaluation?.score || 0), 0) / evaluatedRuns.length
    : 0;
    
  const avgConversationalScore = evaluatedRuns.length > 0
    ? evaluatedRuns.reduce((sum, r) => sum + (r.conversational_evaluation?.score || 0), 0) / evaluatedRuns.length
    : 0;

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
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          {project.name} — Results
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Comprehensive analysis of test execution and evaluation results
        </Typography>
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
            {passedRuns} of {evaluatedRuns.length} passed
          </Typography>
        </Paper>

        <Paper sx={{ p: 3, borderRadius: 2.5, border: "1px solid", borderColor: "divider" }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, display: "block", mb: 1 }}>
            Functional Score
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1.5 }}>
            <Typography variant="h4" sx={{ fontWeight: 800 }}>
              {avgFunctionalScore.toFixed(1)}
            </Typography>
            <CheckCircle2 className="h-5 w-5 text-indigo-500" />
          </Box>
          <LinearProgress
            variant="determinate"
            value={avgFunctionalScore * 10}
            color="primary"
            sx={{ borderRadius: 2, height: 6 }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
            Average across all tests
          </Typography>
        </Paper>

        <Paper sx={{ p: 3, borderRadius: 2.5, border: "1px solid", borderColor: "divider" }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, display: "block", mb: 1 }}>
            Conversational Score
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1.5 }}>
            <Typography variant="h4" sx={{ fontWeight: 800 }}>
              {avgConversationalScore.toFixed(1)}
            </Typography>
            <MessageSquare className="h-5 w-5 text-violet-500" />
          </Box>
          <LinearProgress
            variant="determinate"
            value={avgConversationalScore * 10}
            color="secondary"
            sx={{ borderRadius: 2, height: 6 }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
            Average across all tests
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
                        {run.functional_evaluation.score >= 7 ? (
                          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-500" />
                        )}
                        <Typography variant="body2">
                          Functional: {run.functional_evaluation.score}/10
                        </Typography>
                      </div>
                    )}
                    {run.conversational_evaluation && (
                      <div className="flex items-center gap-1.5">
                        <MessageSquare className="h-4 w-4 text-violet-500" />
                        <Typography variant="body2">
                          Conv: {run.conversational_evaluation.score}/10
                        </Typography>
                      </div>
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
                            {selectedRun.functional_evaluation.score >= 7 ? (
                              <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                            ) : (
                              <XCircle className="h-5 w-5 text-red-500" />
                            )}
                            <Typography variant="body1" sx={{ fontWeight: 600 }}>
                              {selectedRun.functional_evaluation.score >= 7 ? "PASSED" : "FAILED"}
                            </Typography>
                          </div>
                          <Chip
                            label={`${selectedRun.functional_evaluation.score}/10`}
                            color={selectedRun.functional_evaluation.score >= 7 ? "success" : "error"}
                            variant="outlined"
                          />
                        </div>
                        <div>
                          <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>Reasoning</Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ p: 2, bgcolor: "grey.50", borderRadius: 2 }}>
                            {selectedRun.functional_evaluation.reasoning}
                          </Typography>
                        </div>
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
                          <div className="flex items-center justify-between">
                            <Typography variant="body1" sx={{ fontWeight: 600 }}>Score</Typography>
                            <Chip
                              label={`${selectedRun.conversational_evaluation.score}/10`}
                              color={selectedRun.conversational_evaluation.score >= 7 ? "success" : "error"}
                              variant="outlined"
                            />
                          </div>
                        </div>
                        <div>
                          <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>Reasoning</Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ p: 2, bgcolor: "grey.50", borderRadius: 2 }}>
                            {selectedRun.conversational_evaluation.reasoning}
                          </Typography>
                        </div>
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
                        {selectedRun.transcript.split("\n").map((line, idx) => {
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
