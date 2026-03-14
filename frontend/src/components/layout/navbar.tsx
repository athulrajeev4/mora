"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import { FlaskConical, Folder, Home } from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/", icon: Home },
  { name: "Test Suites", href: "/test-suites", icon: FlaskConical },
  { name: "Projects", href: "/projects", icon: Folder },
];

export function Navbar() {
  const pathname = usePathname();

  const activeIndex = navigation.findIndex(
    (item) =>
      pathname === item.href ||
      (item.href !== "/" && pathname.startsWith(item.href))
  );

  return (
    <AppBar
      position="sticky"
      sx={{
        bgcolor: "white",
        color: "text.primary",
        borderBottom: "1px solid",
        borderColor: "divider",
      }}
    >
      <Toolbar
        sx={{
          maxWidth: 1200,
          width: "100%",
          mx: "auto",
          px: { xs: 2, sm: 3, lg: 4 },
          gap: 5,
        }}
      >
        <Link href="/" style={{ textDecoration: "none" }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
            <Box
              sx={{
                width: 34,
                height: 34,
                borderRadius: "10px",
                background: "linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "white",
                fontWeight: 800,
                fontSize: "1rem",
              }}
            >
              M
            </Box>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 800,
                color: "text.primary",
                letterSpacing: "-0.02em",
                fontSize: "1.2rem",
              }}
            >
              Mora
            </Typography>
          </Box>
        </Link>

        <Tabs
          value={activeIndex === -1 ? false : activeIndex}
          sx={{
            minHeight: 64,
            "& .MuiTab-root": {
              minHeight: 64,
              textTransform: "none",
              fontWeight: 500,
              fontSize: "0.9rem",
              color: "text.secondary",
              gap: 1,
              px: 2,
              "&.Mui-selected": {
                color: "primary.main",
                fontWeight: 600,
              },
            },
            "& .MuiTabs-indicator": {
              height: 3,
              borderRadius: "3px 3px 0 0",
              backgroundColor: "primary.main",
            },
          }}
        >
          {navigation.map((item) => {
            const Icon = item.icon;
            return (
              <Tab
                key={item.name}
                component={Link}
                href={item.href}
                icon={<Icon size={18} />}
                iconPosition="start"
                label={item.name}
              />
            );
          })}
        </Tabs>
      </Toolbar>
    </AppBar>
  );
}
