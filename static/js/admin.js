// admin.js 역할
// 관리자 페이지의 탭 전환과 API 호출을 담당한다.
// /admin/tickets, /admin/orders, /admin/refunds를 호출해 표를 채우고,
// 문의 상태 변경만 PATCH /admin/tickets/{id}/status로 반영한다.
// 각 탭은 처음 열릴 때 한 번만 fetch하고 이후엔 캐시된 데이터를 재사용한다.

const TICKET_STATUS_LABELS = {
  open: "접수",
  in_progress: "처리중",
  resolved: "완료",
};

const TICKET_STATUS_BADGE = {
  open: "amber",
  in_progress: "blue",
  resolved: "green",
};

const ORDER_STATUS_LABELS = {
  preparing: "상품 준비 중",
  shipped: "배송 중",
  delivered: "배송 완료",
  cancelled: "주문 취소",
  refunded: "환불 완료",
};

const ORDER_STATUS_BADGE = {
  preparing: "amber",
  shipped: "blue",
  delivered: "green",
  cancelled: "gray",
  refunded: "red",
};

const REFUND_STATUS_LABELS = {
  pending: "접수됨",
};

const state = {
  tickets: null,
  orders: null,
  refunds: null,
};

function badge(label, color) {
  return `<span class="a-badge a-badge--${color}">${label}</span>`;
}

function emptyRow(colspan, text) {
  return `<tr class="admin-empty"><td colspan="${colspan}">${text}</td></tr>`;
}

// ── 문의 관리 ───────────────────────── //

async function loadTickets() {
  const countEl = document.getElementById("tickets-count");
  countEl.textContent = "불러오는 중...";

  try {
    const res = await fetch("/admin/tickets");
    if (!res.ok) throw new Error(`status ${res.status}`);
    const data = await res.json();
    state.tickets = data.tickets;
    renderTickets();
  } catch (err) {
    console.error("[admin] 문의 목록 조회 실패:", err);
    countEl.textContent = "문의 목록을 불러오지 못했어요.";
  }
}

function renderTickets() {
  const tbody = document.getElementById("tickets-tbody");
  const countEl = document.getElementById("tickets-count");
  const filter = document.getElementById("tickets-filter").value;

  const tickets = filter
    ? state.tickets.filter((t) => t.status === filter)
    : state.tickets;

  countEl.textContent = `전체 ${state.tickets.length}건${filter ? ` · ${TICKET_STATUS_LABELS[filter]} ${tickets.length}건` : ""}`;

  if (tickets.length === 0) {
    tbody.innerHTML = emptyRow(6, "해당하는 문의가 없어요.");
    return;
  }

  tbody.innerHTML = tickets
    .map((t) => {
      const options = Object.entries(TICKET_STATUS_LABELS)
        .map(([value, label]) => `<option value="${value}" ${value === t.status ? "selected" : ""}>${label}</option>`)
        .join("");

      return `
        <tr data-ticket-id="${t.id}">
          <td>#${t.id}</td>
          <td>손님 ${t.user_id}번</td>
          <td>${escapeHtml(t.question)}</td>
          <td>${escapeHtml(t.reason)}</td>
          <td>
            ${badge(TICKET_STATUS_LABELS[t.status] ?? t.status, TICKET_STATUS_BADGE[t.status] ?? "gray")}
            <select class="a-status-select" data-ticket-id="${t.id}">
              ${options}
            </select>
          </td>
          <td>${t.created_at}</td>
        </tr>
      `;
    })
    .join("");
}

async function handleStatusChange(event) {
  const select = event.target;
  const ticketId = select.dataset.ticketId;
  const newStatus = select.value;
  const previousStatus = state.tickets.find((t) => String(t.id) === String(ticketId))?.status;

  select.disabled = true;

  try {
    const res = await fetch(`/admin/tickets/${ticketId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus }),
    });

    if (!res.ok) throw new Error(`status ${res.status}`);
    const updated = await res.json();

    const idx = state.tickets.findIndex((t) => t.id === updated.id);
    if (idx !== -1) state.tickets[idx] = updated;
    renderTickets();
  } catch (err) {
    console.error("[admin] 상태 변경 실패:", err);
    alert("상태 변경에 실패했어요. 다시 시도해주세요.");
    if (previousStatus) select.value = previousStatus;
    select.disabled = false;
  }
}

// ── 주문 조회 ───────────────────────── //

async function loadOrders() {
  const countEl = document.getElementById("orders-count");
  countEl.textContent = "불러오는 중...";

  try {
    const res = await fetch("/admin/orders");
    if (!res.ok) throw new Error(`status ${res.status}`);
    const data = await res.json();
    state.orders = data.orders;
    renderOrders();
  } catch (err) {
    console.error("[admin] 주문 목록 조회 실패:", err);
    countEl.textContent = "주문 목록을 불러오지 못했어요.";
  }
}

function renderOrders() {
  const tbody = document.getElementById("orders-tbody");
  const countEl = document.getElementById("orders-count");

  countEl.textContent = `전체 ${state.orders.length}건`;

  if (state.orders.length === 0) {
    tbody.innerHTML = emptyRow(6, "주문 내역이 없어요.");
    return;
  }

  tbody.innerHTML = state.orders
    .map(
      (o) => `
        <tr>
          <td>${o.order_number}</td>
          <td>손님 ${o.user_id}번</td>
          <td>${escapeHtml(o.item_summary)}</td>
          <td>${badge(ORDER_STATUS_LABELS[o.status] ?? o.status, ORDER_STATUS_BADGE[o.status] ?? "gray")}</td>
          <td>${o.total_amount.toLocaleString()}원</td>
          <td>${o.created_at}</td>
        </tr>
      `
    )
    .join("");
}

// ── 환불 요청 ───────────────────────── //

async function loadRefunds() {
  const countEl = document.getElementById("refunds-count");
  countEl.textContent = "불러오는 중...";

  try {
    const res = await fetch("/admin/refunds");
    if (!res.ok) throw new Error(`status ${res.status}`);
    const data = await res.json();
    state.refunds = data.refunds;
    renderRefunds();
  } catch (err) {
    console.error("[admin] 환불 목록 조회 실패:", err);
    countEl.textContent = "환불 목록을 불러오지 못했어요.";
  }
}

function renderRefunds() {
  const tbody = document.getElementById("refunds-tbody");
  const countEl = document.getElementById("refunds-count");

  countEl.textContent = `전체 ${state.refunds.length}건`;

  if (state.refunds.length === 0) {
    tbody.innerHTML = emptyRow(5, "환불 요청이 없어요.");
    return;
  }

  tbody.innerHTML = state.refunds
    .map(
      (r) => `
        <tr>
          <td>${r.order_number}</td>
          <td>손님 ${r.user_id}번</td>
          <td>${escapeHtml(r.reason)}</td>
          <td>${badge(REFUND_STATUS_LABELS[r.status] ?? r.status, "amber")}</td>
          <td>${r.created_at}</td>
        </tr>
      `
    )
    .join("");
}

// ── 공통 ───────────────────────── //

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text ?? "";
  return div.innerHTML;
}

function switchTab(tabName) {
  document.querySelectorAll(".admin-tab").forEach((btn) => {
    const isActive = btn.dataset.tab === tabName;
    btn.classList.toggle("is-active", isActive);
    btn.setAttribute("aria-selected", String(isActive));
  });

  document.querySelectorAll(".admin-panel").forEach((panel) => {
    panel.hidden = panel.id !== `panel-${tabName}`;
  });

  if (tabName === "tickets" && state.tickets === null) loadTickets();
  if (tabName === "orders" && state.orders === null) loadOrders();
  if (tabName === "refunds" && state.refunds === null) loadRefunds();
}

document.querySelectorAll(".admin-tab").forEach((btn) => {
  btn.addEventListener("click", () => switchTab(btn.dataset.tab));
});

document.getElementById("tickets-filter").addEventListener("change", () => {
  if (state.tickets !== null) renderTickets();
});

document.getElementById("tickets-tbody").addEventListener("change", (event) => {
  if (event.target.classList.contains("a-status-select")) {
    handleStatusChange(event);
  }
});

// 첫 화면은 문의 관리 탭이므로 바로 로드
loadTickets();