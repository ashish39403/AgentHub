import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute, PublicOnlyRoute } from './ProtectedRoute';
import { AppShell } from '../components/layout/AppShell';
import { AuthLayout } from '../features/auth/AuthLayout';
import { LoginPage } from '../features/auth/LoginPage';
import { RegisterPage } from '../features/auth/RegisterPage';
import { DashboardPage } from '../features/dashboard/DashboardPage';
import { AgentsListPage } from '../features/agents/AgentsListPage';
import { AgentFormPage } from '../features/agents/AgentFormPage';
import { AgentChatPage } from '../features/chat/AgentChatPage';
import { RoutinesListPage } from '../features/routines/RoutinesListPage';
import { RoutineFormPage } from '../features/routines/RoutineFormPage';
import { RoutineRunDetailsPage } from '../features/routines/RoutineRunDetailsPage';
import { SettingsPage } from '../features/settings/SettingsPage';

export function AppRoutes() {
  return (
    <Routes>
      {/* Public Auth Routes */}
      <Route element={<PublicOnlyRoute />}>
        <Route
          path="/login"
          element={
            <AuthLayout>
              <LoginPage />
            </AuthLayout>
          }
        />
        <Route
          path="/register"
          element={
            <AuthLayout>
              <RegisterPage />
            </AuthLayout>
          }
        />
      </Route>

      {/* Protected App Routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />

          {/* Agents */}
          <Route path="/agents" element={<AgentsListPage />} />
          <Route path="/agents/new" element={<AgentFormPage />} />
          <Route path="/agents/:id/edit" element={<AgentFormPage />} />
          <Route path="/agents/:id/chat" element={<AgentChatPage />} />

          {/* Routines */}
          <Route path="/routines" element={<RoutinesListPage />} />
          <Route path="/routines/new" element={<RoutineFormPage />} />
          <Route path="/routines/:id/edit" element={<RoutineFormPage />} />
          <Route
            path="/routines/:routineId/runs/:runId"
            element={<RoutineRunDetailsPage />}
          />

          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Route>

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
