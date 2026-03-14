import Link from "next/link";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FlaskConical, Folder, ArrowRight, Phone, MessageSquare, BarChart3, CheckCircle2 } from "lucide-react";

export default function HomePage() {
  return (
    <div className="space-y-14">
      {/* Hero Section */}
      <Box sx={{ textAlign: "center", py: 6 }}>
        <Typography
          variant="h3"
          sx={{
            fontWeight: 800,
            letterSpacing: "-0.03em",
            background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #4f46e5 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            mb: 2,
          }}
        >
          Welcome to Mora
        </Typography>
        <Typography
          variant="h5"
          color="text.secondary"
          sx={{ maxWidth: 640, mx: "auto", fontWeight: 400, mb: 1.5 }}
        >
          End-to-end testing and evaluation platform for voice AI agents
        </Typography>
        <Typography
          variant="body1"
          color="text.secondary"
          sx={{ maxWidth: 520, mx: "auto" }}
        >
          Test your voice bots with real phone calls and get AI-powered evaluation feedback
        </Typography>
      </Box>

      {/* Main CTA Card */}
      <Paper
        sx={{
          p: { xs: 4, md: 6 },
          borderRadius: 3,
          border: "1px solid",
          borderColor: "divider",
          background: "linear-gradient(135deg, rgba(79,70,229,0.03) 0%, rgba(124,58,237,0.05) 100%)",
        }}
      >
        <Box sx={{ textAlign: "center", mb: 5 }}>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            Get Started in 2 Steps
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Create your first automated voice test in under 5 minutes
          </Typography>
        </Box>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {/* Step 1 */}
          <Card className="border hover:border-indigo-300 transition-all hover:shadow-md rounded-xl">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-600 text-white font-bold text-sm">
                    1
                  </div>
                  <FlaskConical className="h-5 w-5 text-indigo-600" />
                </div>
                <CheckCircle2 className="h-5 w-5 text-slate-300" />
              </div>
              <CardTitle className="text-lg">Create Test Suite</CardTitle>
              <CardDescription>
                Define test scenarios and expected behaviors for your voice agent
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <ul className="space-y-2.5 text-sm text-slate-500">
                <li className="flex gap-2.5">
                  <span className="text-indigo-400">•</span>
                  <span>Describe the scenario (e.g., &quot;Customer calling about refund&quot;)</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-indigo-400">•</span>
                  <span>Add test cases with caller utterances</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-indigo-400">•</span>
                  <span>Use AI to generate test cases automatically</span>
                </li>
              </ul>
              <Link href="/test-suites/new" className="block">
                <Button className="w-full" size="lg">
                  Create Test Suite
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Step 2 */}
          <Card className="border hover:border-indigo-300 transition-all hover:shadow-md rounded-xl">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-600 text-white font-bold text-sm">
                    2
                  </div>
                  <Folder className="h-5 w-5 text-indigo-600" />
                </div>
                <CheckCircle2 className="h-5 w-5 text-slate-300" />
              </div>
              <CardTitle className="text-lg">Create Project</CardTitle>
              <CardDescription>
                Configure your bot and run automated test calls
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <ul className="space-y-2.5 text-sm text-slate-500">
                <li className="flex gap-2.5">
                  <span className="text-indigo-400">•</span>
                  <span>Enter your bot&apos;s phone number</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-indigo-400">•</span>
                  <span>Select test suites to run</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-indigo-400">•</span>
                  <span>Activate to start real phone calls</span>
                </li>
              </ul>
              <Link href="/projects/new" className="block">
                <Button className="w-full" size="lg">
                  Create Project
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </Paper>

      {/* Features Grid */}
      <Box>
        <Typography
          variant="h4"
          sx={{ textAlign: "center", fontWeight: 700, mb: 5 }}
        >
          How It Works
        </Typography>
        <div className="grid md:grid-cols-3 gap-6">
          <Card className="text-center hover:shadow-md transition-shadow rounded-xl border">
            <CardHeader className="pb-3 pt-8">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50">
                <Phone className="h-7 w-7 text-indigo-600" />
              </div>
              <CardTitle className="text-lg">Automated Phone Calls</CardTitle>
            </CardHeader>
            <CardContent className="pb-8">
              <Typography variant="body2" color="text.secondary">
                System initiates real phone calls to your voice agent using Twilio + LiveKit integration
              </Typography>
            </CardContent>
          </Card>

          <Card className="text-center hover:shadow-md transition-shadow rounded-xl border">
            <CardHeader className="pb-3 pt-8">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50">
                <MessageSquare className="h-7 w-7 text-emerald-600" />
              </div>
              <CardTitle className="text-lg">AI Evaluation</CardTitle>
            </CardHeader>
            <CardContent className="pb-8">
              <Typography variant="body2" color="text.secondary">
                Get functional and conversational quality scores using advanced LLM evaluation
              </Typography>
            </CardContent>
          </Card>

          <Card className="text-center hover:shadow-md transition-shadow rounded-xl border">
            <CardHeader className="pb-3 pt-8">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-50">
                <BarChart3 className="h-7 w-7 text-violet-600" />
              </div>
              <CardTitle className="text-lg">Detailed Reports</CardTitle>
            </CardHeader>
            <CardContent className="pb-8">
              <Typography variant="body2" color="text.secondary">
                Review transcripts, pass/fail results, and actionable feedback for every test call
              </Typography>
            </CardContent>
          </Card>
        </div>
      </Box>

      {/* Quick Links */}
      <Paper
        sx={{
          p: 4,
          borderRadius: 2.5,
          border: "1px solid",
          borderColor: "divider",
        }}
      >
        <Typography variant="h6" sx={{ mb: 2.5 }}>
          Quick Links
        </Typography>
        <div className="flex flex-wrap gap-3">
          <Link href="/test-suites">
            <Button variant="outline">
              <FlaskConical className="h-4 w-4 mr-2" />
              View Test Suites
            </Button>
          </Link>
          <Link href="/projects">
            <Button variant="outline">
              <Folder className="h-4 w-4 mr-2" />
              View Projects
            </Button>
          </Link>
        </div>
      </Paper>
    </div>
  );
}
