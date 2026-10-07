// Tester / Auditor Portal & Evaluation Sandbox

let testerState = {
  activeTab: 'audit',
  selectedGroup: 1,
  dashboardData: null
};

async function renderTesterView() {
  const root = document.getElementById('appRoot');
  root.innerHTML = '<div style="text-align: center; padding: 4rem;">Loading tester dashboard...</div>';

  try {
    const data = await api('/api/tester/dashboard');
    testerState.dashboardData = data;
    renderTesterLayout(data);
    switchTesterTab(testerState.activeTab);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderTesterLayout(data) {
  const root = document.getElementById('appRoot');
  const t = data.tester;
  const m = data.class_metrics;

  root.innerHTML = `
    <!-- Tester Banner -->
    <div class="wellness-hero-banner" style="background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #0d9488 100%);">
      <div class="hero-tagline">
        🔍 Independent QA & Curriculum Evaluator Mode
      </div>
      <h1 class="hero-heading">Welcome, ${t.full_name}</h1>
      <p class="hero-desc">
        You are logged in with independent evaluator credentials (<strong>${t.admission_number}</strong>).
        You are strictly separated from the 69 student class structure and will never be placed in a presentation team.
      </p>
    </div>

    <!-- Metrics Bar -->
    <div class="metrics-grid">
      <div class="metric-card accent-emerald">
        <span class="metric-label">Enrolled Students</span>
        <div class="metric-value">${m.total_enrolled_students} <span class="metric-sub">/ 69 Exact</span></div>
      </div>
      <div class="metric-card accent-teal">
        <span class="metric-label">Completed Surveys</span>
        <div class="metric-value">${m.questionnaires_completed} <span class="metric-sub">/ 69</span></div>
      </div>
      <div class="metric-card accent-indigo">
        <span class="metric-label">Presentation Teams</span>
        <div class="metric-value">${m.groups_count} <span class="metric-sub">Teams</span></div>
      </div>
      <div class="metric-card accent-coral">
        <span class="metric-label">Auditor Role</span>
        <div class="metric-value" style="font-size: 1.25rem; font-weight: 800; color: #6d28d9;">
          Non-Group QA
        </div>
      </div>
    </div>

    <!-- Tester Tabs -->
    <div class="tabs-nav">
      <button class="tab-btn ${testerState.activeTab === 'audit' ? 'active' : ''}" onclick="switchTesterTab('audit')">
        📋 Presentation Teams Audit
      </button>
      <button class="tab-btn ${testerState.activeTab === 'sandbox_q' ? 'active' : ''}" onclick="switchTesterTab('sandbox_q')">
        🧪 Questionnaire Flow Simulator
      </button>
      <button class="tab-btn ${testerState.activeTab === 'workspace_inspect' ? 'active' : ''}" onclick="switchTesterTab('workspace_inspect')">
        👁️ Group Workspace Inspector
      </button>
    </div>

    <!-- Tab Content -->
    <div id="testerTabContent">
      <div style="text-align: center; padding: 2rem;">Loading...</div>
    </div>
  `;
}

function switchTesterTab(tabName) {
  testerState.activeTab = tabName;
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  event?.target?.classList.add('active');

  const content = document.getElementById('testerTabContent');
  if (!content) return;

  if (tabName === 'audit') {
    renderTesterAuditTab(content);
  } else if (tabName === 'sandbox_q') {
    renderTesterSandboxQ(content);
  } else if (tabName === 'workspace_inspect') {
    renderTesterWorkspaceInspect(content);
  }
}

// 1. Teams Audit Tab
function renderTesterAuditTab(container) {
  const groups = testerState.dashboardData?.groups || [];

  container.innerHTML = `
    <div class="card">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;">
        <div>
          <h3 style="font-size: 1.2rem; font-weight: 800; color: #1e1b4b;">10 Wellness Presentation Teams Audit</h3>
          <p style="font-size: 0.825rem; color: var(--text-muted);">
            Inspection view of group allocations, capacity rules (9 of 7, 1 of 6), and presentation readiness checklists.
          </p>
        </div>
        <div>
          <button class="btn btn-secondary btn-sm" onclick="renderTesterView()">🔄 Refresh Live Audit</button>
        </div>
      </div>

      <div class="data-table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Team</th>
              <th>Target Capacity</th>
              <th>Assigned Students</th>
              <th>Assigned Wellness Topic</th>
              <th>Speaking Commitments</th>
              <th>Planned Time (Max 15:00)</th>
              <th>Audit Status</th>
            </tr>
          </thead>
          <tbody>
            ${groups.map(g => `
              <tr>
                <td><strong>Group ${g.group_number}</strong></td>
                <td><span class="badge badge-neutral">${g.max_members} Students</span></td>
                <td>
                  <span class="badge ${g.current_members === g.max_members ? 'badge-primary' : 'badge-warning'}">
                    ${g.current_members} / ${g.max_members}
                  </span>
                </td>
                <td style="font-weight: 700; color: #065f46; max-width: 280px;">${g.topic_title}</td>
                <td>
                  <span class="badge ${g.confirmed_members === g.current_members && g.current_members > 0 ? 'badge-ready' : 'badge-neutral'}">
                    ${g.confirmed_members} / ${g.current_members} Confirmed
                  </span>
                </td>
                <td>
                  <strong>${g.total_duration_formatted}</strong> / 15:00
                </td>
                <td>
                  <span class="badge ${g.is_ready ? 'badge-ready' : 'badge-warning'}">
                    ${g.is_ready ? '✓ PRESENTATION READY' : 'INCOMPLETE'}
                  </span>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

// 2. Questionnaire Sandbox Simulator
function renderTesterSandboxQ(container) {
  container.innerHTML = `
    <div class="card" style="max-width: 780px; margin: 0 auto;">
      <div style="background: linear-gradient(135deg, #059669, #0d9488); padding: 1.25rem 1.5rem; border-radius: var(--radius-md); color: white; margin-bottom: 1.5rem;">
        <h3 style="font-size: 1.2rem; font-weight: 800; margin-bottom: 0.25rem;">Questionnaire Flow Tester (Sandbox Mode)</h3>
        <p style="font-size: 0.85rem; opacity: 0.95;">
          Test the interactive 10-question compatibility questionnaire as an auditor.
          Your responses here demonstrate the student onboarding experience and will not alter the 69 enrolled students.
        </p>
      </div>

      <div class="question-card">
        <div class="question-title">1. How comfortable are you speaking in front of the class?</div>
        <div class="scale-options">
          ${[1, 2, 3, 4, 5].map(v => `<button type="button" class="scale-btn ${v === 4 ? 'selected' : ''}">${v}</button>`).join('')}
        </div>
      </div>

      <div class="question-card">
        <div class="question-title">2. How comfortable are you speaking without reading directly from the PPT?</div>
        <div class="scale-options">
          ${[1, 2, 3, 4, 5].map(v => `<button type="button" class="scale-btn ${v === 5 ? 'selected' : ''}">${v}</button>`).join('')}
        </div>
      </div>

      <div class="question-card">
        <div class="question-title">3. Persona Category during Group Work</div>
        <div class="radio-grid">
          ${["Planner", "Talker", "Creative", "Calm", "Problem solver", "Funny one", "Last-minute survivor", "Depends on the situation"].map(opt => `
            <label class="radio-label ${opt === 'Problem solver' ? 'selected' : ''}">
              <span>${opt}</span>
            </label>
          `).join('')}
        </div>
      </div>

      <div style="text-align: right; margin-top: 1.5rem;">
        <button class="btn btn-primary" onclick="showToast('Sandbox test validated: All questionnaire features operational!', 'success')">
          ✓ Verify Sandbox Questionnaire Submission
        </button>
      </div>
    </div>
  `;
}

// 3. Group Workspace Inspector
async function renderTesterWorkspaceInspect(container) {
  const groups = testerState.dashboardData?.groups || [];

  container.innerHTML = `
    <div class="card">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 0.75rem;">
        <div>
          <h3 style="font-size: 1.2rem; font-weight: 800; color: #1e1b4b;">Inspect Group Collaboration Workspace</h3>
          <p style="font-size: 0.825rem; color: var(--text-muted);">
            View speaking sections, member assignments, and timing allocations for any team.
          </p>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem;">
          <label style="font-size: 0.85rem; font-weight: 700;">Select Team:</label>
          <select id="testerGroupSelect" class="form-control" style="width: auto;" onchange="loadTesterGroupWorkspace(this.value)">
            ${groups.map(g => `
              <option value="${g.id}" ${g.group_number === testerState.selectedGroup ? 'selected' : ''}>
                Group ${g.group_number} - ${g.topic_title}
              </option>
            `).join('')}
          </select>
        </div>
      </div>

      <div id="testerWorkspaceContent">
        <div style="text-align: center; padding: 2rem;">Loading team workspace...</div>
      </div>
    </div>
  `;

  if (groups.length > 0) {
    loadTesterGroupWorkspace(groups[0].id);
  }
}

async function loadTesterGroupWorkspace(groupId) {
  const content = document.getElementById('testerWorkspaceContent');
  if (!content) return;

  try {
    const res = await api(`/api/workspace/group/${groupId}`);
    const g = res.group;
    const members = res.members || [];
    const sections = res.sections || [];
    const check = res.checklist || {};

    content.innerHTML = `
      <div style="background: #f8fafc; border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1.25rem; margin-bottom: 1.25rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; flex-wrap: wrap;">
          <div>
            <h4 style="font-size: 1.15rem; font-weight: 800; color: #065f46;">
              Group ${g.group_number}: ${g.topic_title || 'Topic In Progress'}
            </h4>
            <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.2rem;">
              Enrolled Presenters: <strong>${members.length}</strong> • Planned Time: <strong>${check.total_time_formatted || '0:00'} / 15:00</strong>
            </div>
          </div>
          <span class="badge ${check.is_presentation_ready ? 'badge-ready' : 'badge-warning'}">
            ${check.is_presentation_ready ? '✓ PRESENTATION READY' : 'INCOMPLETE'}
          </span>
        </div>
      </div>

      <h5 style="font-size: 0.95rem; font-weight: 800; margin-bottom: 0.75rem; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.03em;">
        Divided Speaking Sections (${sections.length})
      </h5>
      <div class="data-table-wrapper" style="margin-bottom: 1.5rem;">
        <table class="data-table">
          <thead>
            <tr>
              <th>Order</th>
              <th>Section Title</th>
              <th>Assigned Speaker</th>
              <th>Duration</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            ${sections.length === 0 ? `
              <tr><td colspan="5" style="text-align: center; padding: 2rem; color: var(--text-muted);">No sections created for this group yet.</td></tr>
            ` : sections.map(s => `
              <tr>
                <td><strong>#${s.order_index}</strong></td>
                <td><strong>${s.title}</strong></td>
                <td>${s.presenter_name} (${s.presenter_roll})</td>
                <td>${Math.floor(s.speaking_seconds / 60)}:${(s.speaking_seconds % 60).toString().padStart(2, '0')}</td>
                <td style="font-size: 0.8rem; color: var(--text-muted);">${s.notes || '-'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    content.innerHTML = `<div style="color: var(--danger); padding: 1.5rem;">Could not load group: ${err.message}</div>`;
  }
}
