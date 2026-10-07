// Student View & Interactions

async function renderStudentView() {
  const root = document.getElementById('appRoot');
  root.innerHTML = '<div style="text-align: center; padding: 4rem;">Loading student portal...</div>';

  try {
    const data = await api('/api/student/dashboard');

    if (!data.student.has_completed_questionnaire) {
      renderQuestionnaireView(data.student);
    } else {
      renderStudentDashboardView(data);
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// 1. Questionnaire Rendering & Handling
function renderQuestionnaireView(student) {
  const root = document.getElementById('appRoot');
  root.innerHTML = `
    <div style="max-width: 760px; margin: 1.5rem auto;">
      <div class="card" style="margin-bottom: 1.5rem; background: linear-gradient(135deg, #065f46 0%, #0d9488 50%, #1e3a8a 100%); color: white; border: none; box-shadow: 0 10px 25px rgba(6, 95, 70, 0.25);">
        <div style="display: inline-flex; align-items: center; gap: 0.4rem; background: rgba(255,255,255,0.2); padding: 0.2rem 0.65rem; border-radius: var(--radius-full); font-size: 0.76rem; font-weight: 800; text-transform: uppercase; margin-bottom: 0.5rem;">
          🌿 HEALTH AND WELLNESS - PRESENTATION
        </div>
        <h2 style="font-size: 1.45rem; font-weight: 900; margin-bottom: 0.35rem;">Team Compatibility Questionnaire</h2>
        <p style="font-size: 0.88rem; opacity: 0.95;">
          Welcome, <strong>${student.full_name}</strong> (${student.roll_number})! Please complete this quick 2-minute questionnaire.
          The goal is to help form comfortable, balanced, and diverse presentation teams for our class.
        </p>
      </div>

      <form id="qForm" onsubmit="handleQuestionnaireSubmit(event)">
        <!-- Q1 -->
        <div class="question-card">
          <div class="question-title">1. How comfortable are you speaking in front of the class?</div>
          <div class="question-desc">1 = Very uncomfortable, 5 = Very comfortable</div>
          <div class="scale-options">
            ${[1, 2, 3, 4, 5].map(v => `
              <button type="button" class="scale-btn" onclick="selectScale('q_speaking_comfort', ${v}, this)">${v}</button>
            `).join('')}
          </div>
          <input type="hidden" id="q_speaking_comfort" required />
        </div>

        <!-- Q2 -->
        <div class="question-card">
          <div class="question-title">2. How comfortable are you speaking without reading directly from the PPT?</div>
          <div class="question-desc">1 = Need notes continuously, 5 = Completely fluent without slides</div>
          <div class="scale-options">
            ${[1, 2, 3, 4, 5].map(v => `
              <button type="button" class="scale-btn" onclick="selectScale('q_speaking_no_ppt', ${v}, this)">${v}</button>
            `).join('')}
          </div>
          <input type="hidden" id="q_speaking_no_ppt" required />
        </div>

        <!-- Q3 -->
        <div class="question-card">
          <div class="question-title">3. Which type of person are you during group work?</div>
          <div class="question-desc">Pick the style that best captures your typical natural tendency</div>
          <div class="radio-grid">
            ${[
              "Planner", "Talker", "Creative", "Calm",
              "Problem solver", "Funny one", "Last-minute survivor", "Depends on the situation"
            ].map(opt => `
              <label class="radio-label" onclick="selectRadio('q_persona', '${opt}', this)">
                <input type="radio" name="q_persona_radio" style="display: none;" />
                <span>${opt}</span>
              </label>
            `).join('')}
          </div>
          <input type="hidden" id="q_persona" required />
        </div>

        <!-- Q4 -->
        <div class="question-card">
          <div class="question-title">4. How comfortable are you working with people you don't normally hang out with?</div>
          <div class="question-desc">1 = Prefer only close friends, 5 = Enjoy teaming up with new classmates</div>
          <div class="scale-options">
            ${[1, 2, 3, 4, 5].map(v => `
              <button type="button" class="scale-btn" onclick="selectScale('q_social_comfort', ${v}, this)">${v}</button>
            `).join('')}
          </div>
          <input type="hidden" id="q_social_comfort" required />
        </div>

        <!-- Q5 -->
        <div class="question-card">
          <div class="question-title">5. Do you prefer a group atmosphere that is:</div>
          <div class="radio-grid" style="grid-template-columns: repeat(3, 1fr);">
            ${["Very energetic", "Calm", "Balanced"].map(opt => `
              <label class="radio-label" onclick="selectRadio('q_atmosphere', '${opt}', this)">
                <input type="radio" name="q_atmosphere_radio" style="display: none;" />
                <span>${opt}</span>
              </label>
            `).join('')}
          </div>
          <input type="hidden" id="q_atmosphere" required />
        </div>

        <!-- Q6 -->
        <div class="question-card">
          <div class="question-title">6. How comfortable are you taking the lead when necessary?</div>
          <div class="question-desc">1 = Prefer following, 5 = Ready to coordinate and drive next steps</div>
          <div class="scale-options">
            ${[1, 2, 3, 4, 5].map(v => `
              <button type="button" class="scale-btn" onclick="selectScale('q_leadership_comfort', ${v}, this)">${v}</button>
            `).join('')}
          </div>
          <input type="hidden" id="q_leadership_comfort" required />
        </div>

        <!-- Q7 -->
        <div class="question-card">
          <div class="question-title">7. What matters most for a good group?</div>
          <div class="radio-grid">
            ${[
              "Good communication", "Similar interests", "Different strengths",
              "Friendly atmosphere", "Everyone contributing", "Good planning"
            ].map(opt => `
              <label class="radio-label" onclick="selectRadio('q_priority', '${opt}', this)">
                <input type="radio" name="q_priority_radio" style="display: none;" />
                <span>${opt}</span>
              </label>
            `).join('')}
          </div>
          <input type="hidden" id="q_priority" required />
        </div>

        <!-- FUN Q1 -->
        <div class="question-card">
          <div class="question-title">🎉 Fun Scenario 1: Your group's PPT suddenly stops working 2 minutes before the presentation. What do you do?</div>
          <div class="radio-grid">
            ${[
              "Continue without PPT",
              "Start explaining confidently",
              "Make a joke and recover",
              "Ask another member to handle it",
              "Panic internally but continue",
              '"This was part of our plan."'
            ].map(opt => `
              <label class="radio-label" onclick="selectRadio('q_fun_ppt_crash', '${opt}', this)">
                <input type="radio" name="q_fun_ppt_crash_radio" style="display: none;" />
                <span>${opt}</span>
              </label>
            `).join('')}
          </div>
          <input type="hidden" id="q_fun_ppt_crash" required />
        </div>

        <!-- FUN Q2 -->
        <div class="question-card">
          <div class="question-title">⚡ Fun Scenario 2: Your group has 10 minutes left and half the work isn't finished. You are:</div>
          <div class="radio-grid">
            ${[
              "The person making a plan",
              "The person doing the work",
              "The person motivating everyone",
              'The person saying "don\'t worry"',
              "The person somehow fixing everything",
              'The person asking "what happened?"'
            ].map(opt => `
              <label class="radio-label" onclick="selectRadio('q_fun_10min_rush', '${opt}', this)">
                <input type="radio" name="q_fun_10min_rush_radio" style="display: none;" />
                <span>${opt}</span>
              </label>
            `).join('')}
          </div>
          <input type="hidden" id="q_fun_10min_rush" required />
        </div>

        <!-- FUN Q3 -->
        <div class="question-card">
          <div class="question-title">💡 Fun Question 3: If your group had a team name, what would it be?</div>
          <div class="question-desc">Allow a short, fun suggestion</div>
          <input type="text" id="q_fun_team_name" class="form-control" placeholder="e.g. The Synergy Squad, Kinetic Presenters..." required />
        </div>

        <div style="text-align: right; margin-top: 1.5rem;">
          <button type="submit" class="btn btn-primary btn-lg">Submit Questionnaire & Continue →</button>
        </div>
      </form>
    </div>
  `;
}

function selectScale(inputId, value, btnElem) {
  document.getElementById(inputId).value = value;
  const container = btnElem.parentElement;
  container.querySelectorAll('.scale-btn').forEach(b => b.classList.remove('selected'));
  btnElem.classList.add('selected');
}

function selectRadio(inputId, value, labelElem) {
  document.getElementById(inputId).value = value;
  const container = labelElem.parentElement;
  container.querySelectorAll('.radio-label').forEach(l => l.classList.remove('selected'));
  labelElem.classList.add('selected');
}

async function handleQuestionnaireSubmit(e) {
  e.preventDefault();

  const requiredFields = [
    'q_speaking_comfort', 'q_speaking_no_ppt', 'q_persona', 'q_social_comfort',
    'q_atmosphere', 'q_leadership_comfort', 'q_priority', 'q_fun_ppt_crash',
    'q_fun_10min_rush', 'q_fun_team_name'
  ];

  for (const f of requiredFields) {
    const val = document.getElementById(f).value;
    if (!val) {
      showToast('Please answer all questions before submitting', 'error');
      return;
    }
  }

  const payload = {
    q_speaking_comfort: parseInt(document.getElementById('q_speaking_comfort').value),
    q_speaking_no_ppt: parseInt(document.getElementById('q_speaking_no_ppt').value),
    q_persona: document.getElementById('q_persona').value,
    q_social_comfort: parseInt(document.getElementById('q_social_comfort').value),
    q_atmosphere: document.getElementById('q_atmosphere').value,
    q_leadership_comfort: parseInt(document.getElementById('q_leadership_comfort').value),
    q_priority: document.getElementById('q_priority').value,
    q_fun_ppt_crash: document.getElementById('q_fun_ppt_crash').value,
    q_fun_10min_rush: document.getElementById('q_fun_10min_rush').value,
    q_fun_team_name: document.getElementById('q_fun_team_name').value
  };

  try {
    await api('/api/student/questionnaire', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    showToast('Questionnaire recorded! Loading your dashboard...', 'success');
    renderStudentView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// 2. Main Student Dashboard
function renderStudentDashboardView(data) {
  const root = document.getElementById('appRoot');
  const student = data.student;
  const group = data.group;
  const members = data.members || [];
  const mySection = data.my_section;
  const progress = data.progress || {};

  root.innerHTML = `
    <div style="max-width: 1100px; margin: 0 auto;">
      <!-- Welcome Header Card -->
      <div class="card" style="background: white; border-left: 5px solid var(--primary); padding: 1.5rem;">
        <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 1rem;">
          <div>
            <div style="font-size: 0.8rem; font-weight: 800; text-transform: uppercase; color: #059669; letter-spacing: 0.04em;">
              🌿 HEALTH AND WELLNESS - PRESENTATION
            </div>
            <h1 style="font-size: 1.6rem; font-weight: 800; color: #1e1b4b; margin-top: 0.15rem;">
              Welcome, ${student.full_name}
            </h1>
            <div style="display: flex; gap: 0.75rem; margin-top: 0.35rem; font-size: 0.85rem; color: var(--text-muted);">
              <span>Admission: <strong>${student.admission_number}</strong></span>
              <span>•</span>
              <span>Roll: <strong>${student.roll_number}</strong></span>
              <span>•</span>
              <span>Questionnaire: <strong style="color: var(--success);">Completed ✓</strong></span>
            </div>
          </div>

          <div>
            ${student.my_confirmed ? `
              <div class="badge badge-ready" style="font-size: 0.85rem; padding: 0.45rem 0.95rem;">
                ✓ Speaking Commitment Confirmed
              </div>
            ` : `
              <button class="btn btn-primary" onclick="confirmMySpeaking()">
                🗣️ Click to Confirm: "I WILL SPEAK"
              </button>
            `}
          </div>
        </div>
      </div>

      ${!data.groups_finalized ? `
        <!-- Groups Pending Finalization -->
        <div class="card" style="text-align: center; padding: 3rem 1.5rem;">
          <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">⚖️</div>
          <h3 style="font-size: 1.25rem; font-weight: 800; color: #1e1b4b;">Group Allocation in Progress</h3>
          <p style="color: var(--text-muted); max-width: 540px; margin: 0.5rem auto 1.25rem auto; font-size: 0.9rem;">
            Your questionnaire responses have been recorded. The course coordinator is currently running the
            balancing algorithm to organize 10 fair, comfortable groups.
          </p>
          <div class="badge badge-warning">Awaiting Professor Finalization</div>
        </div>
      ` : `
        <!-- Groups Finalized View -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.25rem; margin-bottom: 1.5rem;">
          
          <!-- Group & Topic Card -->
          <div class="card" style="margin-bottom: 0;">
            <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted);">Assigned Team</div>
            <div style="font-size: 1.5rem; font-weight: 800; color: var(--primary); margin: 0.2rem 0 0.75rem 0;">
              Group ${group.group_number}
              <span style="font-size: 0.85rem; font-weight: 600; color: var(--text-muted);">(${group.member_count} Members)</span>
            </div>
            
            <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted);">Assigned Topic</div>
            <div style="font-size: 1.05rem; font-weight: 800; color: #1e1b4b; margin: 0.2rem 0 0.35rem 0;">
              ${group.topic_title}
            </div>
            <p style="font-size: 0.825rem; color: var(--text-muted); line-height: 1.4;">
              ${group.topic_description || "Every group receives exactly one unique presentation topic."}
            </p>
          </div>

          <!-- My Speaking Section Card -->
          <div class="card" style="margin-bottom: 0;">
            <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted);">Your Speaking Role</div>
            ${mySection ? `
              <div style="font-size: 1.25rem; font-weight: 800; color: #1e1b4b; margin: 0.2rem 0 0.35rem 0;">
                ${mySection.title}
              </div>
              <div style="font-size: 0.85rem; font-weight: 600; color: var(--accent); margin-bottom: 0.5rem;">
                ⏱️ Speaking Time: ${mySection.speaking_time_formatted} (${mySection.speaking_seconds} seconds)
              </div>
              <div style="font-size: 0.8rem; color: var(--text-muted); background: var(--bg-subtle); padding: 0.5rem 0.75rem; border-radius: var(--radius-sm);">
                <strong>Notes:</strong> ${mySection.notes || "No notes added yet."}
              </div>
            ` : `
              <div style="padding: 1rem 0; color: var(--text-muted); font-size: 0.875rem;">
                ⚠️ You have not been assigned a speaking section yet.<br>
                Coordinate with your group below to add your section!
              </div>
            `}
          </div>

          <!-- Presentation Progress & Timer Card -->
          <div class="card" style="margin-bottom: 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
              <span style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted);">Presentation Status</span>
              <span class="badge ${progress.is_presentation_ready ? 'badge-ready' : progress.is_over_time ? 'badge-danger' : 'badge-warning'}">
                ${progress.is_presentation_ready ? '✓ PRESENTATION READY' : progress.is_over_time ? '⚠️ OVER TIME' : 'IN PROGRESS'}
              </span>
            </div>

            <div style="margin-bottom: 0.75rem;">
              <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.25rem;">
                <span>Total Planned Time:</span>
                <span style="color: ${progress.is_over_time ? 'var(--danger)' : 'var(--text-main)'}; font-weight: 800;">
                  ${progress.total_duration_formatted} / ${progress.max_duration_formatted}
                </span>
              </div>
              <div class="progress-track">
                <div class="progress-fill ${progress.is_over_time ? 'danger' : progress.is_presentation_ready ? 'success' : ''}"
                     style="width: ${Math.min(100, (progress.total_duration_seconds / progress.max_duration_seconds) * 100)}%;">
                </div>
              </div>
            </div>

            <div style="font-size: 0.8rem; color: var(--text-muted);">
              <div>Participation: <strong>${progress.confirmed_members} / ${progress.total_members} confirmed</strong></div>
              <div>Topic Coverage: <strong>${progress.all_assigned ? 'All members assigned ✓' : 'Sections unassigned'}</strong></div>
            </div>
          </div>
        </div>

        <!-- Collaborative Workspace Section -->
        <div class="card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;">
            <div>
              <h3 style="font-size: 1.15rem; font-weight: 800; color: #1e1b4b;">Presentation Planner & Speaking Sections</h3>
              <p style="font-size: 0.8rem; color: var(--text-muted);">
                Rule: Every member MUST speak. Divide your topic into structured speaking segments within 15 minutes.
              </p>
            </div>
            <button class="btn btn-accent btn-sm" onclick="openAddSectionModal(${group.group_id})">
              + Add Speaking Section
            </button>
          </div>

          <div class="data-table-wrapper" id="sectionsTableWrapper">
            <!-- Rendered by loadGroupSections -->
            <div style="text-align: center; padding: 2rem;">Loading planner sections...</div>
          </div>
        </div>

        <!-- Group Members Roster Card -->
        <div class="card">
          <h3 style="font-size: 1.15rem; font-weight: 800; color: #1e1b4b; margin-bottom: 0.75rem;">
            Group ${group.group_number} Members
          </h3>
          <div class="data-table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Roll No</th>
                  <th>Member Name</th>
                  <th>Admission No</th>
                  <th>Assigned Sections</th>
                  <th>Total Time</th>
                  <th>Speaking Commitment</th>
                </tr>
              </thead>
              <tbody>
                ${members.map(m => `
                  <tr style="${m.is_self ? 'background-color: #f5f3ff;' : ''}">
                    <td><strong>${m.roll_number}</strong></td>
                    <td>
                      ${m.full_name}
                      ${m.is_self ? '<span class="badge badge-primary" style="margin-left: 0.35rem;">You</span>' : ''}
                    </td>
                    <td>${m.admission_number}</td>
                    <td>${m.sections_summary}</td>
                    <td>${Math.floor(m.speaking_time_total / 60)}m ${m.speaking_time_total % 60}s</td>
                    <td>
                      ${m.is_confirmed ? `
                        <span class="badge badge-ready">✓ Confirmed</span>
                      ` : `
                        <span class="badge badge-warning">Pending</span>
                      `}
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `}
    </div>
  `;

  if (data.groups_finalized && group) {
    loadGroupSections(group.group_id);
  }
}

// 3. Collaborative Sections Management
async function loadGroupSections(groupId) {
  try {
    const res = await api(`/api/workspace/group/${groupId}`);
    const wrapper = document.getElementById('sectionsTableWrapper');
    if (!wrapper) return;

    const sections = res.sections || [];
    const members = res.members || [];
    window.currentGroupMembers = members; // Cache for dropdown in modal

    if (sections.length === 0) {
      wrapper.innerHTML = `
        <div style="text-align: center; padding: 2.5rem; color: var(--text-muted);">
          No speaking sections added yet. Click <strong>+ Add Speaking Section</strong> above to assign topics!
        </div>
      `;
      return;
    }

    wrapper.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>Order</th>
            <th>Section Title</th>
            <th>Presenter</th>
            <th>Duration</th>
            <th>Notes</th>
            <th style="text-align: right;">Actions</th>
          </tr>
        </thead>
        <tbody>
          ${sections.map((sec, idx) => `
            <tr>
              <td><strong>#${idx + 1}</strong></td>
              <td><strong>${sec.title}</strong></td>
              <td>${sec.presenter_name} (${sec.presenter_roll})</td>
              <td>${Math.floor(sec.speaking_seconds / 60)}:${(sec.speaking_seconds % 60).toString().padStart(2, '0')}</td>
              <td style="color: var(--text-muted); max-width: 260px; font-size: 0.8rem;">${sec.notes || '-'}</td>
              <td style="text-align: right;">
                <button class="btn btn-secondary btn-sm" onclick="openEditSectionModal(${JSON.stringify(sec).replace(/"/g, '&quot;')})">Edit</button>
                <button class="btn btn-outline-danger btn-sm" onclick="deleteSection(${sec.id}, ${groupId})">Delete</button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function openAddSectionModal(groupId) {
  const members = window.currentGroupMembers || [];
  openModal(`
    <div class="modal-header">
      <h3 class="modal-title">Add Speaking Section</h3>
      <button class="btn-close" onclick="closeModal()">×</button>
    </div>
    <form onsubmit="handleCreateSection(event, ${groupId})">
      <div class="form-group">
        <label class="form-label">Presenter</label>
        <select id="secPresenter" class="form-control" required>
          <option value="">Select Group Member...</option>
          ${members.map(m => `
            <option value="${m.id}">${m.full_name} (${m.roll_number})</option>
          `).join('')}
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Section Title</label>
        <input type="text" id="secTitle" class="form-control" placeholder="e.g. Introduction & Problem Definition" required />
      </div>

      <div class="form-group" style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
        <div>
          <label class="form-label">Minutes</label>
          <input type="number" id="secMinutes" class="form-control" min="0" max="15" value="2" required />
        </div>
        <div>
          <label class="form-label">Seconds</label>
          <input type="number" id="secSeconds" class="form-control" min="0" max="59" value="0" required />
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Key Points / Speaking Notes (Optional)</label>
        <textarea id="secNotes" class="form-control" rows="3" placeholder="Bullet points for the speaker"></textarea>
      </div>

      <div style="text-align: right; margin-top: 1rem;">
        <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Save Section</button>
      </div>
    </form>
  `);
}

function openEditSectionModal(sec) {
  const members = window.currentGroupMembers || [];
  const mins = Math.floor(sec.speaking_seconds / 60);
  const secs = sec.speaking_seconds % 60;

  openModal(`
    <div class="modal-header">
      <h3 class="modal-title">Edit Speaking Section</h3>
      <button class="btn-close" onclick="closeModal()">×</button>
    </div>
    <form onsubmit="handleUpdateSection(event, ${sec.id}, ${sec.group_id})">
      <div class="form-group">
        <label class="form-label">Presenter</label>
        <select id="secPresenterEdit" class="form-control" required>
          ${members.map(m => `
            <option value="${m.id}" ${m.id === sec.student_id ? 'selected' : ''}>${m.full_name} (${m.roll_number})</option>
          `).join('')}
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Section Title</label>
        <input type="text" id="secTitleEdit" class="form-control" value="${sec.title}" required />
      </div>

      <div class="form-group" style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
        <div>
          <label class="form-label">Minutes</label>
          <input type="number" id="secMinutesEdit" class="form-control" min="0" max="15" value="${mins}" required />
        </div>
        <div>
          <label class="form-label">Seconds</label>
          <input type="number" id="secSecondsEdit" class="form-control" min="0" max="59" value="${secs}" required />
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Key Points / Speaking Notes</label>
        <textarea id="secNotesEdit" class="form-control" rows="3">${sec.notes || ''}</textarea>
      </div>

      <div style="text-align: right; margin-top: 1rem;">
        <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn btn-primary">Update Section</button>
      </div>
    </form>
  `);
}

async function handleCreateSection(e, groupId) {
  e.preventDefault();
  const studentId = parseInt(document.getElementById('secPresenter').value);
  const title = document.getElementById('secTitle').value.trim();
  const mins = parseInt(document.getElementById('secMinutes').value || 0);
  const secs = parseInt(document.getElementById('secSeconds').value || 0);
  const totalSecs = (mins * 60) + secs;
  const notes = document.getElementById('secNotes').value.trim();

  if (totalSecs < 30) {
    showToast('Speaking duration must be at least 30 seconds', 'error');
    return;
  }

  try {
    await api(`/api/workspace/group/${groupId}/sections`, {
      method: 'POST',
      body: JSON.stringify({
        student_id: studentId,
        title,
        speaking_seconds: totalSecs,
        notes
      })
    });
    closeModal();
    showToast('Speaking section added!', 'success');
    renderStudentView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function handleUpdateSection(e, sectionId, groupId) {
  e.preventDefault();
  const studentId = parseInt(document.getElementById('secPresenterEdit').value);
  const title = document.getElementById('secTitleEdit').value.trim();
  const mins = parseInt(document.getElementById('secMinutesEdit').value || 0);
  const secs = parseInt(document.getElementById('secSecondsEdit').value || 0);
  const totalSecs = (mins * 60) + secs;
  const notes = document.getElementById('secNotesEdit').value.trim();

  try {
    await api(`/api/workspace/sections/${sectionId}`, {
      method: 'PUT',
      body: JSON.stringify({
        student_id: studentId,
        title,
        speaking_seconds: totalSecs,
        notes
      })
    });
    closeModal();
    showToast('Section updated!', 'success');
    renderStudentView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteSection(sectionId, groupId) {
  if (!confirm('Are you sure you want to delete this speaking section?')) return;
  try {
    await api(`/api/workspace/sections/${sectionId}`, { method: 'DELETE' });
    showToast('Section removed', 'info');
    renderStudentView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function confirmMySpeaking() {
  try {
    await api('/api/student/confirm_speaking', { method: 'POST' });
    showToast('Your speaking commitment has been confirmed! ✓', 'success');
    renderStudentView();
  } catch (err) {
    showToast(err.message, 'error');
  }
}
