// Admin Dashboard & Management System

let adminState = {
  activeTab: 'generator',
  metrics: {},
  groups: [],
  students: [],
  constraints: [],
  topics: [],
  fairnessReport: []
};

async function renderAdminView() {
  const root = document.getElementById('appRoot');
  root.innerHTML = '<div style="text-align: center; padding: 4rem;">Loading administrator dashboard...</div>';

  try {
    await fetchAdminMetrics();
    renderAdminLayout();
    switchAdminTab(adminState.activeTab);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function fetchAdminMetrics() {
  adminState.metrics = await api('/api/admin/metrics');
}

function renderAdminLayout() {
  const root = document.getElementById('appRoot');
  const m = adminState.metrics;

  root.innerHTML = `
    <!-- Wellness Coordinator Banner -->
    <div class="wellness-hero-banner">
      <div class="hero-tagline">🌿 Course Leadership Portal</div>
      <h1 class="hero-heading">Ahmed Sabith • Presentation Hub Coordinator</h1>
      <p class="hero-desc">
        Managing 69 students across 10 balanced wellness presentation teams.
        Audit group harmony, configure constraints, assign 10 unique topics, and track speaking readiness in real time.
      </p>
    </div>

    <!-- Top Metrics Overview Bar -->
    <div class="metrics-grid">
      <div class="metric-card accent-emerald">
        <span class="metric-label">Enrolled Students</span>
        <div class="metric-value">${m.total_students} <span class="metric-sub">/ ${m.target_students}</span></div>
      </div>

      <div class="metric-card accent-teal">
        <span class="metric-label">Completed Surveys</span>
        <div class="metric-value">${m.questionnaires_completed} <span class="metric-sub">/ 69</span></div>
      </div>

      <div class="metric-card accent-indigo">
        <span class="metric-label">Assigned Students</span>
        <div class="metric-value">${m.students_assigned} <span class="metric-sub">/ 69</span></div>
      </div>

      <div class="metric-card accent-amber">
        <span class="metric-label">Assigned Topics</span>
        <div class="metric-value">${m.topics_assigned} <span class="metric-sub">/ 10</span></div>
      </div>

      <div class="metric-card ${m.presentation_ready_groups === 10 ? 'accent-emerald' : 'accent-coral'}">
        <span class="metric-label">Ready Teams</span>
        <div class="metric-value">${m.presentation_ready_groups} <span class="metric-sub">/ 10 Teams</span></div>
      </div>
    </div>

    <!-- Quick Action / Demo Banner -->
    <div class="card" style="background: #f8fafc; border: 1px dashed #cbd5e1; padding: 0.85rem 1.25rem; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 0.75rem;">
      <div style="font-size: 0.85rem;">
        <strong>🚀 Evaluation Quick-Actions:</strong> Run one-click end-to-end simulation or reset anytime.
      </div>
      <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
        <button class="btn btn-secondary btn-sm" onclick="seedSampleQuestionnaires()">
          📝 Auto-Fill 69 Sample Questionnaires
        </button>
        <button class="btn btn-accent btn-sm" onclick="simulateCompleteFlow()">
          ✨ 1-Click Simulate Full Presentation Flow (All 10 Ready)
        </button>
        <button class="btn btn-secondary btn-sm" onclick="resetClassData()">
          🔄 Reset Class
        </button>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="tabs-nav">
      <button class="tab-btn ${adminState.activeTab === 'generator' ? 'active' : ''}" onclick="switchAdminTab('generator')">
        👥 10-Group Balance Board
      </button>
      <button class="tab-btn ${adminState.activeTab === 'fairness' ? 'active' : ''}" onclick="switchAdminTab('fairness')">
        ⚖️ Fairness Diagnostic Report
      </button>
      <button class="tab-btn ${adminState.activeTab === 'topics' ? 'active' : ''}" onclick="switchAdminTab('topics')">
        📚 Topic Allocation (10 Topics)
      </button>
      <button class="tab-btn ${adminState.activeTab === 'constraints' ? 'active' : ''}" onclick="switchAdminTab('constraints')">
        🔗 Constraints (Together / Apart)
      </button>
      <button class="tab-btn ${adminState.activeTab === 'students' ? 'active' : ''}" onclick="switchAdminTab('students')">
        🎓 Student Roster (69 Students)
      </button>
      <button class="tab-btn ${adminState.activeTab === 'export' ? 'active' : ''}" onclick="switchAdminTab('export')">
        📊 Export & Print
      </button>
    </div>

    <!-- Tab Content Root -->
    <div id="adminTabContent">
      <div style="text-align: center; padding: 3rem;">Loading section...</div>
    </div>
  `;
}

function switchAdminTab(tabName) {
  adminState.activeTab = tabName;
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  event?.target?.classList.add('active');

  const content = document.getElementById('adminTabContent');
  if (!content) return;

  if (tabName === 'generator') {
    renderGroupGeneratorTab(content);
  } else if (tabName === 'fairness') {
    renderFairnessTab(content);
  } else if (tabName === 'topics') {
    renderTopicsTab(content);
  } else if (tabName === 'constraints') {
    renderConstraintsTab(content);
  } else if (tabName === 'students') {
    renderStudentsTab(content);
  } else if (tabName === 'export') {
    renderExportTab(content);
  }
}

// ----------------------------------------------------
// 1. Group Generator & Balance Board Tab
// ----------------------------------------------------
async function renderGroupGeneratorTab(container) {
  container.innerHTML = '<div style="text-align: center; padding: 2rem;">Loading group distribution...</div>';
  try {
    const res = await api('/api/admin/groups');
    adminState.groups = res.groups || [];
    const canUndo = res.can_undo;
    const isFinalized = adminState.metrics.groups_are_finalized;

    container.innerHTML = `
      <!-- Generator Toolbar -->
      <div class="card" style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 1rem;">
        <div>
          <h3 style="font-size: 1.15rem; font-weight: 800; color: #1e1b4b;">Group Generation & Review</h3>
          <p style="font-size: 0.8rem; color: var(--text-muted);">
            Rule Structure: 9 groups of 7 students + 1 group of 6 students (Total 69).
            ${isFinalized ? '<strong style="color: var(--success);">✓ Groups Finalized (Visible to students)</strong>' : '<span style="color: var(--warning);">Draft state (Hidden from students until finalized)</span>'}
          </p>
        </div>

        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
          <button class="btn btn-primary" onclick="generateGroups()">
            ⚡ ${adminState.groups.some(g => g.members.length > 0) ? 'Regenerate Groups' : 'Generate Balanced Groups'}
          </button>
          ${canUndo ? `
            <button class="btn btn-secondary" onclick="undoGroupChanges()">
              ↩ Undo
            </button>
          ` : ''}
          ${isFinalized ? `
            <button class="btn btn-secondary" onclick="unfinalizeGroups()">
              🔓 Unfinalize
            </button>
          ` : `
            <button class="btn btn-accent" onclick="finalizeGroups()">
              ✓ Finalize 10 Groups
            </button>
          `}
        </div>
      </div>

      <!-- 10 Groups Grid -->
      <div class="groups-grid">
        ${adminState.groups.map(g => renderGroupCard(g)).join('')}
      </div>
    `;
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderGroupCard(g) {
  const m = g.metrics || {};
  const isGroup10 = g.group_number === 10;
  const targetCap = isGroup10 ? 6 : 7;
  const isFull = g.member_count === targetCap;

  return `
    <div class="group-card">
      <div class="group-header">
        <div class="group-title">
          <span>Group ${g.group_number}</span>
          <span class="badge ${isFull ? 'badge-primary' : 'badge-warning'}">
            ${g.member_count} / ${targetCap} Members
          </span>
          ${g.is_locked ? '<span title="Group Locked">🔒</span>' : ''}
        </div>
        <div>
          <button class="btn btn-secondary btn-sm" onclick="toggleGroupLock(${g.id})">
            ${g.is_locked ? 'Unlock Group' : 'Lock Group'}
          </button>
        </div>
      </div>

      <!-- Admin Diagnostic Score (Strictly Admin Only) -->
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
        <span class="score-badge">
          ★ Balance Score: ${m.balance_score || 0}/100
        </span>
        <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600;">
          Avg Speaking: ${m.speaking_avg || '-'} / 5.0
        </span>
      </div>

      <div class="summary-text">
        ${m.summary || 'Unassigned group'}
      </div>

      <div class="group-topic-box">
        <small>Assigned Topic</small>
        ${g.topic_title || 'Not Assigned Yet'}
      </div>

      <!-- Members Roster -->
      <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.35rem;">
        Group Members (${g.member_count})
      </div>
      <ul class="members-list">
        ${g.members.length === 0 ? `
          <li style="padding: 1rem 0; text-align: center; color: var(--text-light); font-size: 0.85rem;">
            No students assigned yet
          </li>
        ` : g.members.map(s => `
          <li class="member-item">
            <div class="member-info">
              <span class="member-roll">${s.roll_number}</span>
              <span style="font-weight: 600;">${s.full_name}</span>
              ${s.is_locked ? '<span title="Student Locked">🔒</span>' : ''}
              ${s.confirmed_at ? '<span title="Speaking Confirmed" style="color: var(--success); font-weight: bold;">✓</span>' : ''}
            </div>
            <div class="member-actions">
              <button class="btn btn-secondary btn-sm" style="padding: 0.15rem 0.4rem; font-size: 0.7rem;" onclick="openMoveStudentModal(${s.id}, ${g.id}, '${s.full_name}')">
                Move
              </button>
              <button class="btn btn-secondary btn-sm" style="padding: 0.15rem 0.4rem; font-size: 0.7rem;" onclick="openSwapStudentModal(${s.id}, '${s.full_name}')">
                Swap
              </button>
            </div>
          </li>
        `).join('')}
      </ul>

      <!-- Presentation Readiness Indicator -->
      <div style="margin-top: auto; padding-top: 0.75rem; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem;">
        <span style="color: var(--text-muted);">
          Time: <strong>${g.presentation_status?.total_duration_formatted || '0:00'}</strong> / 15:00
        </span>
        <span class="badge ${g.presentation_status?.is_ready ? 'badge-ready' : 'badge-neutral'}">
          ${g.presentation_status?.is_ready ? '✓ READY' : 'INCOMPLETE'}
        </span>
      </div>
    </div>
  `;
}

// ----------------------------------------------------
// 2. Fairness Diagnostic Report Tab
// ----------------------------------------------------
async function renderFairnessTab(container) {
  container.innerHTML = '<div style="text-align: center; padding: 2rem;">Computing fairness diagnostics...</div>';
  try {
    const res = await api('/api/admin/fairness_report');
    const report = res.groups_fairness || [];

    container.innerHTML = `
      <div class="card">
        <h3 style="font-size: 1.15rem; font-weight: 800; color: #1e1b4b; margin-bottom: 0.25rem;">
          Diagnostic Fairness & Balance Report
        </h3>
        <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 1.25rem;">
          ADMIN DIAGNOSTIC ONLY: Verifies even speaker confidence distribution, leadership balance, and working style entropy across all 10 groups. Individual student scores are never exposed.
        </p>

        <div class="data-table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Group</th>
                <th>Capacity</th>
                <th>Speaking Avg</th>
                <th>No-PPT Avg</th>
                <th>Social Comfort</th>
                <th>Leadership</th>
                <th>Anchor Leaders</th>
                <th>Working Styles</th>
                <th>Balance Score</th>
                <th>Compatibility Diagnosis</th>
              </tr>
            </thead>
            <tbody>
              ${report.map(r => `
                <tr>
                  <td><strong>Group ${r.group_number}</strong></td>
                  <td>
                    <span class="badge ${r.current_members === r.target_members ? 'badge-ready' : 'badge-warning'}">
                      ${r.current_members} / ${r.target_members}
                    </span>
                  </td>
                  <td><strong>${r.speaking_avg}</strong> / 5.0</td>
                  <td>${r.no_ppt_avg}</td>
                  <td>${r.social_avg}</td>
                  <td>${r.leadership_avg}</td>
                  <td>${r.leaders_count}</td>
                  <td>${r.unique_personas} distinct styles</td>
                  <td>
                    <span class="score-badge">
                      ${r.balance_score}/100
                    </span>
                  </td>
                  <td style="font-size: 0.8rem; color: var(--text-muted);">${r.compatibility_summary}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ----------------------------------------------------
// 3. Topic Allocation Tab
// ----------------------------------------------------
async function renderTopicsTab(container) {
  container.innerHTML = '<div style="text-align: center; padding: 2rem;">Loading topics...</div>';
  try {
    const res = await api('/api/admin/topics');
    const topics = res.topics || [];

    container.innerHTML = `
      <div class="card" style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 1rem;">
        <div>
          <h3 style="font-size: 1.15rem; font-weight: 800; color: #1e1b4b;">Presentation Topics Allocation</h3>
          <p style="font-size: 0.8rem; color: var(--text-muted);">
            Exactly 10 predefined topics. Each group receives exactly ONE unique topic.
          </p>
        </div>

        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
          <button class="btn btn-secondary" onclick="assignTopicsRandom()">
            🎲 Option A: Random Topic Draw
          </button>
          <button class="btn btn-primary" onclick="assignTopicsPreference()">
            🎯 Option B: Preference-Based Allocation
          </button>
        </div>
      </div>

      <div class="data-table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Topic Title</th>
              <th>Description / Scope</th>
              <th>Assigned Group</th>
              <th style="text-align: right;">Manual Override</th>
            </tr>
          </thead>
          <tbody>
            ${topics.map((t, idx) => `
              <tr>
                <td><strong>${idx + 1}</strong></td>
                <td><strong style="color: #1e1b4b;">${t.title}</strong></td>
                <td style="font-size: 0.8rem; color: var(--text-muted); max-width: 380px;">${t.description}</td>
                <td>
                  ${t.assigned_group_number ? `
                    <span class="badge badge-primary">Group ${t.assigned_group_number}</span>
                  ` : `
                    <span class="badge badge-neutral">Unassigned</span>
                  `}
                </td>
                <td style="text-align: right;">
                  <button class="btn btn-secondary btn-sm" onclick="openManualTopicModal(${t.id}, '${t.title.replace(/'/g, "\\'")}')">
                    Assign to Group
                  </button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ----------------------------------------------------
// 4. Constraints Manager Tab (Keep Together / Apart)
// ----------------------------------------------------
async function renderConstraintsTab(container) {
  container.innerHTML = '<div style="text-align: center; padding: 2rem;">Loading constraints...</div>';
  try {
    const [constraints, students] = await Promise.all([
      api('/api/admin/constraints'),
      api('/api/admin/students')
    ]);
    adminState.constraints = constraints;
    adminState.students = students;

    container.innerHTML = `
      <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;">
          <div>
            <h3 style="font-size: 1.15rem; font-weight: 800; color: #1e1b4b;">Friend & Separation Constraints</h3>
            <p style="font-size: 0.8rem; color: var(--text-muted);">
              Configure "Keep Together" or "Keep Apart" rules. The balancing algorithm enforces these unless mathematically impossible.
            </p>
          </div>
          <button class="btn btn-primary btn-sm" onclick="openAddConstraintModal()">
            + Add New Constraint
          </button>
        </div>

        <div class="data-table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Constraint Type</th>
                <th>Student A</th>
                <th>Student B</th>
                <th>Configured On</th>
                <th style="text-align: right;">Action</th>
              </tr>
            </thead>
            <tbody>
              ${constraints.length === 0 ? `
                <tr>
                  <td colspan="5" style="text-align: center; padding: 2rem; color: var(--text-muted);">
                    No constraints added yet. Click <strong>+ Add New Constraint</strong> to specify pairs.
                  </td>
                </tr>
              ` : constraints.map(c => `
                <tr>
                  <td>
                    <span class="badge ${c.constraint_type === 'TOGETHER' ? 'badge-primary' : 'badge-danger'}">
                      ${c.constraint_type === 'TOGETHER' ? '🤝 KEEP TOGETHER' : '⚡ KEEP APART'}
                    </span>
                  </td>
                  <td><strong>${c.student_a_name}</strong> (${c.student_a_roll})</td>
                  <td><strong>${c.student_b_name}</strong> (${c.student_b_roll})</td>
                  <td style="color: var(--text-muted); font-size: 0.8rem;">${c.created_at || 'Saved'}</td>
                  <td style="text-align: right;">
                    <button class="btn btn-outline-danger btn-sm" onclick="deleteConstraint(${c.id})">
                      Remove
                    </button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ----------------------------------------------------
// 5. Student Roster Tab
// ----------------------------------------------------
async function renderStudentsTab(container) {
  container.innerHTML = '<div style="text-align: center; padding: 2rem;">Loading student roster...</div>';
  try {
    const students = await api('/api/admin/students');
    adminState.students = students;

    container.innerHTML = `
      <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;">
          <div>
            <h3 style="font-size: 1.15rem; font-weight: 800; color: #1e1b4b;">Class Roster (69 Students)</h3>
            <p style="font-size: 0.8rem; color: var(--text-muted);">
              Manage student profiles, reset passwords, lock to groups, or inspect completion status.
            </p>
          </div>
          <button class="btn btn-primary btn-sm" onclick="openAddStudentModal()">
            + Add Student
          </button>
        </div>

        <div class="data-table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Roll No</th>
                <th>Admission No</th>
                <th>Student Name</th>
                <th>Questionnaire</th>
                <th>Assigned Group</th>
                <th>Assigned Topic</th>
                <th>Speaking Confirmed</th>
                <th style="text-align: right;">Actions</th>
              </tr>
            </thead>
            <tbody>
              ${students.map(s => `
                <tr>
                  <td><strong>${s.roll_number}</strong></td>
                  <td><code>${s.admission_number}</code></td>
                  <td>${s.full_name}</td>
                  <td>
                    ${s.questionnaire_completed ? `
                      <span class="badge badge-ready">Done ✓</span>
                    ` : `
                      <span class="badge badge-warning">Pending</span>
                    `}
                  </td>
                  <td>
                    ${s.group_number ? `
                      <span class="badge badge-primary">Group ${s.group_number}</span>
                    ` : `
                      <span class="badge badge-neutral">Unassigned</span>
                    `}
                  </td>
                  <td style="font-size: 0.8rem; max-width: 220px; color: var(--text-muted);">
                    ${s.topic_title || '-'}
                  </td>
                  <td>
                    ${s.speaking_confirmed ? `
                      <span class="badge badge-ready">✓ Yes</span>
                    ` : `
                      <span class="badge badge-neutral">Pending</span>
                    `}
                  </td>
                  <td style="text-align: right;">
                    <button class="btn btn-secondary btn-sm" onclick="openEditStudentModal(${JSON.stringify(s).replace(/"/g, '&quot;')})">Edit</button>
                    <button class="btn btn-secondary btn-sm" onclick="openResetPasswordModal(${s.id}, '${s.full_name}')">Reset Pwd</button>
                    <button class="btn btn-outline-danger btn-sm" onclick="deleteStudent(${s.id})">Del</button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ----------------------------------------------------
// 6. Export CSV & Print Tab
// ----------------------------------------------------
function renderExportTab(container) {
  container.innerHTML = `
    <div class="card" style="max-width: 700px; margin: 1rem auto; text-align: center; padding: 2.5rem 1.5rem;">
      <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📄</div>
      <h3 style="font-size: 1.3rem; font-weight: 800; color: #1e1b4b; margin-bottom: 0.5rem;">
        Export Class Presentation Roster
      </h3>
      <p style="font-size: 0.875rem; color: var(--text-muted); max-width: 500px; margin: 0 auto 1.5rem auto;">
        Download the official class list including all 69 students, their 10 assigned groups, topics, speaking sections, and confirmation readiness.
      </p>

      <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap;">
        <a href="/api/admin/export/csv" class="btn btn-primary btn-lg" download>
          📥 Download CSV Spreadsheet
        </a>
        <button class="btn btn-secondary btn-lg" onclick="window.print()">
          🖨️ Print View
        </button>
      </div>
    </div>
  `;
}

// ----------------------------------------------------
// Admin Operations
// ----------------------------------------------------

async function generateGroups() {
  try {
    const res = await api('/api/admin/groups/generate', { method: 'POST' });
    showToast(res.message, 'success');
    renderAdminView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function undoGroupChanges() {
  try {
    const res = await api('/api/admin/groups/undo', { method: 'POST' });
    showToast(res.message, 'info');
    renderAdminView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function finalizeGroups() {
  try {
    const res = await api('/api/admin/groups/finalize', { method: 'POST' });
    showToast(res.message, 'success');
    renderAdminView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function unfinalizeGroups() {
  try {
    const res = await api('/api/admin/groups/unfinalize', { method: 'POST' });
    showToast(res.message, 'info');
    renderAdminView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function toggleGroupLock(groupId) {
  try {
    const res = await api(`/api/admin/groups/${groupId}/toggle_lock`, { method: 'POST' });
    showToast(res.is_locked ? 'Group locked' : 'Group unlocked', 'info');
    renderAdminView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function assignTopicsRandom() {
  try {
    const res = await api('/api/admin/topics/assign_random', { method: 'POST' });
    showToast(res.message, 'success');
    renderAdminView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function assignTopicsPreference() {
  try {
    const res = await api('/api/admin/topics/assign_preference', { method: 'POST' });
    showToast(res.message, 'success');
    renderAdminView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function seedSampleQuestionnaires() {
  try {
    const res = await api('/api/admin/seed_sample_questionnaires', { method: 'POST' });
    showToast(res.message, 'success');
    renderAdminView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function simulateCompleteFlow() {
  try {
    const res = await api('/api/admin/simulate_complete_flow', { method: 'POST' });
    showToast(res.message, 'success');
    renderAdminView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function resetClassData() {
  if (!confirm('Are you sure you want to reset all class data to initial pristine state?')) return;
  try {
    const res = await api('/api/admin/reset_class', { method: 'POST' });
    showToast(res.message, 'info');
    renderAdminView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ----------------------------------------------------
// Modals for Move, Swap, Constraints, Topics, Students
// ----------------------------------------------------

function openMoveStudentModal(studentId, currentGroupId, studentName) {
  const groups = adminState.groups;
  openModal(`
    <div class="modal-header">
      <h3 class="modal-title">Move Student to Group</h3>
      <button class="btn-close" onclick="closeModal()">×</button>
    </div>
    <form onsubmit="handleMoveStudent(event, ${studentId})">
      <p style="font-size: 0.875rem; margin-bottom: 1rem;">
        Moving: <strong>${studentName}</strong>
      </p>
      <div class="form-group">
        <label class="form-label">Target Group</label>
        <select id="moveTargetGroup" class="form-control" required>
          ${groups.filter(g => g.id !== currentGroupId).map(g => `
            <option value="${g.id}">Group ${g.group_number} (${g.member_count}/${g.max_members} members)</option>
          `).join('')}
        </select>
      </div>
      <div style="text-align: right; margin-top: 1.25rem;">
        <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Confirm Move</button>
      </div>
    </form>
  `);
}

async function handleMoveStudent(e, studentId) {
  e.preventDefault();
  const targetGroupId = parseInt(document.getElementById('moveTargetGroup').value);
  try {
    await api('/api/admin/groups/move_student', {
      method: 'POST',
      body: JSON.stringify({ student_id: studentId, target_group_id: targetGroupId })
    });
    closeModal();
    showToast('Student moved successfully', 'success');
    renderAdminView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function openSwapStudentModal(studentId, studentName) {
  const allStudents = adminState.students.length > 0 ? adminState.students : [];
  openModal(`
    <div class="modal-header">
      <h3 class="modal-title">Swap Students</h3>
      <button class="btn-close" onclick="closeModal()">×</button>
    </div>
    <form onsubmit="handleSwapStudents(event, ${studentId})">
      <p style="font-size: 0.875rem; margin-bottom: 1rem;">
        Swap <strong>${studentName}</strong> with another classmate:
      </p>
      <div class="form-group">
        <label class="form-label">Select Peer to Swap With</label>
        <select id="swapTargetStudent" class="form-control" required>
          <option value="">Choose classmate...</option>
          ${allStudents.filter(s => s.id !== studentId).map(s => `
            <option value="${s.id}">${s.full_name} (${s.roll_number}) - Group ${s.group_number || 'None'}</option>
          `).join('')}
        </select>
      </div>
      <div style="text-align: right; margin-top: 1.25rem;">
        <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Confirm Swap</button>
      </div>
    </form>
  `);
}

async function handleSwapStudents(e, studentAId) {
  e.preventDefault();
  const studentBId = parseInt(document.getElementById('swapTargetStudent').value);
  try {
    await api('/api/admin/groups/swap_students', {
      method: 'POST',
      body: JSON.stringify({ student_a_id: studentAId, student_b_id: studentBId })
    });
    closeModal();
    showToast('Students swapped successfully', 'success');
    renderAdminView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function openManualTopicModal(topicId, topicTitle) {
  const groups = adminState.groups;
  openModal(`
    <div class="modal-header">
      <h3 class="modal-title">Assign Topic</h3>
      <button class="btn-close" onclick="closeModal()">×</button>
    </div>
    <form onsubmit="handleManualTopicAssign(event, ${topicId})">
      <p style="font-size: 0.875rem; margin-bottom: 1rem;">
        Assigning: <strong>${topicTitle}</strong>
      </p>
      <div class="form-group">
        <label class="form-label">Select Group</label>
        <select id="manualTopicGroup" class="form-control" required>
          ${groups.map(g => `
            <option value="${g.id}">Group ${g.group_number} (Currently: ${g.topic_title || 'None'})</option>
          `).join('')}
        </select>
      </div>
      <div style="text-align: right; margin-top: 1.25rem;">
        <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Assign Topic</button>
      </div>
    </form>
  `);
}

async function handleManualTopicAssign(e, topicId) {
  e.preventDefault();
  const groupId = parseInt(document.getElementById('manualTopicGroup').value);
  try {
    await api('/api/admin/topics/assign_manual', {
      method: 'POST',
      body: JSON.stringify({ group_id: groupId, topic_id: topicId })
    });
    closeModal();
    showToast('Topic assigned to Group!', 'success');
    renderAdminView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function openAddConstraintModal() {
  const students = adminState.students;
  openModal(`
    <div class="modal-header">
      <h3 class="modal-title">Add Constraint Rule</h3>
      <button class="btn-close" onclick="closeModal()">×</button>
    </div>
    <form onsubmit="handleAddConstraint(event)">
      <div class="form-group">
        <label class="form-label">Rule Type</label>
        <select id="constraintType" class="form-control" required>
          <option value="TOGETHER">🤝 Keep Together (Must be in same group)</option>
          <option value="APART">⚡ Keep Apart (Must be in separate groups)</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Student A</label>
        <select id="constraintStudentA" class="form-control" required>
          <option value="">Select Student A...</option>
          ${students.map(s => `<option value="${s.id}">${s.full_name} (${s.roll_number})</option>`).join('')}
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Student B</label>
        <select id="constraintStudentB" class="form-control" required>
          <option value="">Select Student B...</option>
          ${students.map(s => `<option value="${s.id}">${s.full_name} (${s.roll_number})</option>`).join('')}
        </select>
      </div>
      <div style="text-align: right; margin-top: 1.25rem;">
        <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Add Constraint</button>
      </div>
    </form>
  `);
}

async function handleAddConstraint(e) {
  e.preventDefault();
  const aId = parseInt(document.getElementById('constraintStudentA').value);
  const bId = parseInt(document.getElementById('constraintStudentB').value);
  const cType = document.getElementById('constraintType').value;

  try {
    await api('/api/admin/constraints', {
      method: 'POST',
      body: JSON.stringify({ student_a_id: aId, student_b_id: bId, constraint_type: cType })
    });
    closeModal();
    showToast('Constraint saved successfully', 'success');
    renderAdminView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteConstraint(id) {
  try {
    await api(`/api/admin/constraints/${id}`, { method: 'DELETE' });
    showToast('Constraint deleted', 'info');
    renderAdminView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function openAddStudentModal() {
  openModal(`
    <div class="modal-header">
      <h3 class="modal-title">Add Student</h3>
      <button class="btn-close" onclick="closeModal()">×</button>
    </div>
    <form onsubmit="handleAddStudent(event)">
      <div class="form-group">
        <label class="form-label">Full Name</label>
        <input type="text" id="addFullName" class="form-control" placeholder="e.g. Student 070" required />
      </div>
      <div class="form-group">
        <label class="form-label">Roll Number</label>
        <input type="text" id="addRollNumber" class="form-control" placeholder="e.g. R70" required />
      </div>
      <div class="form-group">
        <label class="form-label">Admission Number</label>
        <input type="text" id="addAdmNumber" class="form-control" placeholder="e.g. ADM2026070" required />
      </div>
      <div class="form-group">
        <label class="form-label">Email (Optional)</label>
        <input type="email" id="addEmail" class="form-control" placeholder="student@college.edu" />
      </div>
      <div style="text-align: right; margin-top: 1.25rem;">
        <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Add Student</button>
      </div>
    </form>
  `);
}

async function handleAddStudent(e) {
  e.preventDefault();
  const fullName = document.getElementById('addFullName').value.trim();
  const roll = document.getElementById('addRollNumber').value.trim();
  const adm = document.getElementById('addAdmNumber').value.trim();
  const email = document.getElementById('addEmail').value.trim();

  try {
    await api('/api/admin/students', {
      method: 'POST',
      body: JSON.stringify({ full_name: fullName, roll_number: roll, admission_number: adm, email })
    });
    closeModal();
    showToast('Student added successfully', 'success');
    renderAdminView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function openEditStudentModal(s) {
  openModal(`
    <div class="modal-header">
      <h3 class="modal-title">Edit Student</h3>
      <button class="btn-close" onclick="closeModal()">×</button>
    </div>
    <form onsubmit="handleEditStudent(event, ${s.id})">
      <div class="form-group">
        <label class="form-label">Full Name</label>
        <input type="text" id="editFullName" class="form-control" value="${s.full_name}" required />
      </div>
      <div class="form-group">
        <label class="form-label">Roll Number</label>
        <input type="text" id="editRollNumber" class="form-control" value="${s.roll_number}" required />
      </div>
      <div class="form-group">
        <label class="form-label">Admission Number</label>
        <input type="text" id="editAdmNumber" class="form-control" value="${s.admission_number}" required />
      </div>
      <div class="form-group">
        <label class="form-label">Email</label>
        <input type="email" id="editEmail" class="form-control" value="${s.email || ''}" />
      </div>
      <div style="text-align: right; margin-top: 1.25rem;">
        <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Update Profile</button>
      </div>
    </form>
  `);
}

async function handleEditStudent(e, studentId) {
  e.preventDefault();
  const fullName = document.getElementById('editFullName').value.trim();
  const roll = document.getElementById('editRollNumber').value.trim();
  const adm = document.getElementById('editAdmNumber').value.trim();
  const email = document.getElementById('editEmail').value.trim();

  try {
    await api(`/api/admin/students/${studentId}`, {
      method: 'PUT',
      body: JSON.stringify({ full_name: fullName, roll_number: roll, admission_number: adm, email })
    });
    closeModal();
    showToast('Student profile updated', 'success');
    renderAdminView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function openResetPasswordModal(studentId, studentName) {
  openModal(`
    <div class="modal-header">
      <h3 class="modal-title">Reset Password</h3>
      <button class="btn-close" onclick="closeModal()">×</button>
    </div>
    <form onsubmit="handleResetPassword(event, ${studentId})">
      <p style="font-size: 0.875rem; margin-bottom: 1rem;">
        Reset password for: <strong>${studentName}</strong>
      </p>
      <div class="form-group">
        <label class="form-label">New Password</label>
        <input type="password" id="resetNewPwd" class="form-control" placeholder="Enter new password" required />
      </div>
      <div style="text-align: right; margin-top: 1.25rem;">
        <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Save New Password</button>
      </div>
    </form>
  `);
}

async function handleResetPassword(e, studentId) {
  e.preventDefault();
  const newPwd = document.getElementById('resetNewPwd').value.trim();
  try {
    await api(`/api/admin/students/${studentId}/reset_password`, {
      method: 'POST',
      body: JSON.stringify({ new_password: newPwd })
    });
    closeModal();
    showToast('Password reset successfully', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteStudent(studentId) {
  if (!confirm('Are you sure you want to remove this student?')) return;
  try {
    await api(`/api/admin/students/${studentId}`, { method: 'DELETE' });
    showToast('Student deleted', 'info');
    renderAdminView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}
