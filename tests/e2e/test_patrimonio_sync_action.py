"""Browser contract for F60's Patrimônio sync action.

F59 responses are intercepted so these tests exercise only the dashboard
choreography: start, bounded polling, safe terminal states, and handoff to
the existing import review modal.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page, Route

from tests.support.import_flow import login_and_select_italo

from .selectors import SELECTORS

ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "visual" / "artifacts"
ARTIFACT_PATH = ARTIFACT_DIR / "f60-atualizar-posicao-patrimonio.png"


def _login(page: Page, live_url: str) -> None:
    login_and_select_italo(page, live_url)
    page.wait_for_selector(SELECTORS["dashboard_sync_btn"], state="visible", timeout=8_000)


def _seed_class(page: Page) -> None:
    page.evaluate(
        """async () => {
            const response = await fetch('/api/classes', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: 'Acoes', target_pct: 100}),
            });
            if (!response.ok) throw new Error('class seed failed: ' + response.status);
        }"""
    )
    page.reload()
    page.wait_for_selector(SELECTORS["dashboard_sync_btn"], state="visible", timeout=8_000)


def _preview() -> dict[str, object]:
    return {
        "preview_id": "f60-preview-1",
        "auto_matched": [
            {
                "broker_ticker": "PETR4",
                "name": "PETR4",
                "asset_class_id": 1,
                "buy_enabled": True,
                "sell_enabled": True,
                "currency_code": "BRL",
            }
        ],
        "unmatched": [],
        "asset_classes": [{"id": 1, "name": "Acoes", "color": "#2563eb"}],
    }


def _capture(page: Page, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path), full_page=True)


class TestPatrimonioSyncAction:
    def test_local_post_r42_browser_acceptance(self, page: Page) -> None:
        """Exercise F60 client state with local simulated responses only.

        This acceptance intentionally avoids the authenticated app server. It
        loads the production Alpine store source into a local browser harness,
        intercepts fetch in-page, and renders the production notification
        attributes needed for the UI contract.
        """
        template_path = (
            Path(__file__).resolve().parents[2]
            / "src"
            / "omaha"
            / "templates"
            / "_patrimonio_add_asset_modal.html"
        )
        template_source = template_path.read_text(encoding="utf-8")
        store_script = template_source.split("<script>", 1)[1].split("</script>", 1)[0]
        store_script = "\n".join(
            "window.__assetClasses = [];"
            if line.lstrip().startswith("window.__assetClasses")
            else line
            for line in store_script.splitlines()
        )

        page.set_content(
            """
            <section data-testid="patrimonio-actions" data-sync-state="idle">
              <button type="button" data-testid="dashboard-sync-btn"></button>
              <div data-testid="patrimonio-notifications"></div>
            </section>
            <div data-testid="import-modal-overlay" hidden></div>
            """
        )
        page.add_script_tag(
            content="""
            window.Alpine = {
              stores: {},
              store: function (name, value) {
                if (arguments.length === 2) this.stores[name] = value;
                return this.stores[name];
              },
            };
            """
        )
        page.evaluate(
            """
            (source) => {
              (0, eval)(source);
              document.dispatchEvent(new Event('alpine:init'));
            }
            """,
            store_script,
        )
        assert page.evaluate("Object.keys(window.Alpine.stores)") == [
            "classSum",
            "importModal",
            "patrimonioSync",
            "addAssetModal",
            "newClassModal",
        ]
        page.evaluate(
            """
            () => {
              const selectors = {
                actions: '[data-testid="patrimonio-actions"]',
                button: '[data-testid="dashboard-sync-btn"]',
                outlet: '[data-testid="patrimonio-notifications"]',
                card: '[data-testid="patrimonio-notification"]',
                close: '[data-testid="patrimonio-notification-close"]',
                modal: '[data-testid="import-modal-overlay"]',
              };
              window.renderF60 = () => {
                const sync = Alpine.store('patrimonioSync');
                const actions = document.querySelector(selectors.actions);
                const button = document.querySelector(selectors.button);
                const outlet = document.querySelector(selectors.outlet);
                actions.dataset.syncState = sync.state;
                button.disabled = sync.state === 'loading';
                outlet.replaceChildren(...sync.notifications.map((item) => {
                  const card = document.createElement('article');
                  card.className = 'patrimonio-notification patrimonio-notification--' + item.type;
                  card.dataset.testid = 'patrimonio-notification';
                  card.dataset.notificationId = String(item.id);
                  card.setAttribute('role', item.role);
                  card.setAttribute('aria-live', item.live);
                  card.setAttribute('aria-atomic', 'true');
                  card.addEventListener(
                    'mouseenter',
                    () => sync.setNotificationInteraction(item.id, 'hovered', true),
                  );
                  card.addEventListener(
                    'mouseleave',
                    () => sync.setNotificationInteraction(item.id, 'hovered', false),
                  );
                  card.addEventListener(
                    'focusin',
                    () => sync.setNotificationInteraction(item.id, 'focused', true),
                  );
                  card.addEventListener(
                    'focusout',
                    () => sync.setNotificationInteraction(item.id, 'focused', false),
                  );
                  const copy = document.createElement('p');
                  copy.textContent = item.message;
                  card.append(copy);
                  const close = document.createElement('button');
                  close.type = 'button';
                  close.dataset.testid = 'patrimonio-notification-close';
                  close.setAttribute('aria-label', 'Fechar notificação');
                  close.addEventListener('click', () => {
                    sync.dismissNotification(item.id, true);
                    window.renderF60();
                  });
                  card.append(close);
                  return card;
                }));
                document.querySelector(selectors.modal).hidden = !Alpine.store('importModal').open;
              };
              Alpine.store('patrimonioSync').pollDelay = 0;
              Alpine.store('patrimonioSync').init(null);
              window.renderF60();
            }
            """
        )

        page.locator(SELECTORS["patrimonio_notification_close"]).first.focus()
        page.locator(SELECTORS["patrimonio_notification"]).dispatch_event("mouseenter")
        page.evaluate(
            """
            () => {
              const sync = Alpine.store('patrimonioSync');
              const startResponse = new Promise((resolve) => { window.resolveF60Start = resolve; });
              window.f60Requests = [];
              window.fetch = (url, options = {}) => {
                window.f60Requests.push({url, method: options.method || 'GET'});
                if (options.method === 'POST') return startResponse;
                return Promise.resolve({ok: true, json: () => Promise.resolve({
                  job_id: 'local-job', status: 'succeeded', preview: {
                    preview_id: 'local-preview', auto_matched: [], unmatched: [], asset_classes: [],
                  }, error: null,
                })});
              };
              sync.start();
              window.renderF60();
            }
            """
        )
        loading = page.locator(SELECTORS["patrimonio_notification"])
        assert loading.count() == 1
        assert loading.inner_text().strip() == "Atualizando posição..."
        assert (
            page.locator(SELECTORS["patrimonio_actions"]).get_attribute("data-sync-state")
            == "loading"
        )
        assert loading.get_attribute("role") == "status"
        assert loading.get_attribute("aria-live") == "polite"
        loading.dispatch_event("mouseenter")
        page.evaluate("Alpine.store('patrimonioSync').start()")
        assert (
            page.evaluate("window.f60Requests.filter((item) => item.method === 'POST').length") == 1
        )

        page.evaluate(
            """
            () => window.resolveF60Start({
              ok: true,
              json: () => Promise.resolve({job_id: 'local-job', status: 'queued'}),
            })
            """
        )
        page.wait_for_function(
            "() => Alpine.store('patrimonioSync').state === 'success'",
            timeout=3_000,
        )
        page.wait_for_function(
            "() => Alpine.store('importModal').open === true",
            timeout=3_000,
        )
        page.evaluate("window.renderF60()")
        success = page.locator(SELECTORS["patrimonio_notification"])
        assert success.count() == 1
        assert (
            success.inner_text().strip()
            == "Atualização concluída. Revise posições antes de confirmar"
        )
        assert success.get_attribute("role") == "status"
        assert success.get_attribute("aria-live") == "polite"
        assert page.locator(SELECTORS["import_modal_overlay"]).get_attribute("hidden") is None
        assert page.evaluate("Alpine.store('importModal').open") is True
        assert page.evaluate("Alpine.store('importModal').step") == 2
        assert (
            page.evaluate("window.f60Requests.filter((item) => item.method === 'POST').length") == 1
        )
        assert (
            page.evaluate(
                "window.f60Requests.some((item) => item.url.includes('/api/import/commit'))"
            )
            is False
        )

        page.evaluate("Alpine.store('importModal').closeModal()")
        page.wait_for_timeout(50)
        page.evaluate("window.renderF60()")
        assert (
            page.locator(SELECTORS["patrimonio_actions"]).get_attribute("data-sync-state") == "idle"
        )
        assert page.locator(SELECTORS["patrimonio_notification"]).count() == 0
        assert page.evaluate("document.activeElement?.dataset.testid") == "dashboard-sync-btn"

        page.evaluate("Alpine.store('patrimonioSync').init(null); window.renderF60()")
        idle = page.locator(SELECTORS["patrimonio_notification"])
        idle.hover()
        page.wait_for_timeout(8_100)
        page.evaluate("window.renderF60()")
        assert page.locator(SELECTORS["patrimonio_notification"]).count() == 1
        page.locator(SELECTORS["patrimonio_notification_close"]).click()
        assert page.locator(SELECTORS["patrimonio_notification"]).count() == 0

        # Ordinary focused-card dismissal remains protected when no newer
        # lifecycle card replaces it; replacement above removed interacted idle
        # and loading cards and emitted one fresh success card.
        page.evaluate("Alpine.store('patrimonioSync').init(null); window.renderF60()")
        page.locator(SELECTORS["patrimonio_notification_close"]).first.focus()
        focused_id = page.locator(SELECTORS["patrimonio_notification"]).get_attribute(
            "data-notification-id"
        )
        page.evaluate(
            "(id) => Alpine.store('patrimonioSync').dismissNotification(Number(id))", focused_id
        )
        assert page.locator(SELECTORS["patrimonio_notification"]).count() == 1
        page.locator(SELECTORS["patrimonio_notification_close"]).first.evaluate("(el) => el.blur()")
        assert page.evaluate("Alpine.store('patrimonioSync').notifications[0].focused") is False
        page.evaluate(
            "(id) => Alpine.store('patrimonioSync').dismissNotification(Number(id), true)",
            focused_id,
        )
        page.evaluate("window.renderF60()")
        assert page.locator(SELECTORS["patrimonio_notification"]).count() == 0

        # Error lifecycle replacement also removes an interacted loading card
        # and emits exactly one assertive safe card.
        page.evaluate(
            """
            () => {
              const sync = Alpine.store('patrimonioSync');
              window.fetch = (url, options = {}) => {
                window.f60Requests.push({url, method: options.method || 'GET'});
                if (options.method === 'POST') {
                  return Promise.resolve({
                    ok: true,
                    json: () =>
                      Promise.resolve({job_id: 'error-job', status: 'queued'}),
                  });
                }
                return Promise.resolve({ok: true, json: () => Promise.resolve({
                  job_id: 'error-job', status: 'failed', preview: null,
                  error: {message: 'Não foi possível baixar o CSV do MyProfit.'},
                })});
              };
              sync.start();
            }
            """
        )
        page.wait_for_function(
            "() => Alpine.store('patrimonioSync').state === 'error'", timeout=3_000
        )
        page.evaluate("window.renderF60()")
        error = page.locator(SELECTORS["patrimonio_notification"])
        assert error.count() == 1
        assert error.inner_text().strip() == "Não foi possível baixar o CSV do MyProfit."
        assert error.get_attribute("role") == "alert"
        assert error.get_attribute("aria-live") == "assertive"

    def test_state_markers_render(self, page: Page, live_url: str) -> None:
        _login(page, live_url)
        action = page.locator(SELECTORS["patrimonio_actions"])
        assert action.get_attribute("data-sync-state") == "idle"
        assert action.locator("button").nth(0).get_attribute("data-testid") == "dashboard-sync-btn"
        assert (
            action.locator("button").nth(1).get_attribute("data-testid") == "dashboard-import-btn"
        )
        assert action.locator("[data-testid=dashboard-sync-btn] .icon").inner_text() == "sync"
        notification = page.locator(SELECTORS["patrimonio_notification"]).first
        assert notification.inner_text().strip() == "Pronto para atualizar posição."
        assert notification.get_attribute("role") == "status"
        assert notification.get_attribute("aria-live") == "polite"
        assert notification.get_attribute("aria-atomic") == "true"
        assert notification.get_attribute("data-notification-id")

    def test_start_and_poll_without_navigation(self, page: Page, live_url: str) -> None:
        _login(page, live_url)
        _seed_class(page)
        requests: list[tuple[str, str]] = []
        poll_responses = iter(
            [
                {"job_id": "job-1", "status": "queued", "preview": None, "error": None},
                {"job_id": "job-1", "status": "running", "preview": None, "error": None},
                {
                    "job_id": "job-1",
                    "status": "succeeded",
                    "preview": _preview(),
                    "error": None,
                },
            ]
        )

        def start(route: Route) -> None:
            requests.append((route.request.method, route.request.url))
            route.fulfill(status=202, json={"job_id": "job-1", "status": "queued"})

        def poll(route: Route) -> None:
            requests.append((route.request.method, route.request.url))
            route.fulfill(status=200, json=next(poll_responses))

        page.route("**/api/myprofit/sync", start)
        page.route("**/api/myprofit/sync/*", poll)
        original_url = page.url
        page.click(SELECTORS["dashboard_sync_btn"])
        page.wait_for_function(
            "() => document.querySelector('[data-testid=\"patrimonio-actions\"]')"
            ".dataset.syncState === 'loading'"
        )
        assert page.locator(SELECTORS["dashboard_sync_btn"]).is_disabled()
        page.evaluate(
            "document.querySelector('[data-testid=\"dashboard-sync-btn\"]')"
            ".dispatchEvent(new MouseEvent('click', {bubbles: true}))"
        )
        page.wait_for_function(
            "() => document.querySelector('[data-testid=\"patrimonio-actions\"]')"
            ".dataset.syncState === 'success'",
            timeout=8_000,
        )
        page.locator(SELECTORS["import_modal_overlay"]).wait_for(state="visible", timeout=2_000)
        assert page.url == original_url
        assert requests[0][0] == "POST"
        assert [method for method, _url in requests].count("POST") == 1
        assert len(requests) == 4
        assert page.locator(SELECTORS["import_commit_btn"]).is_visible()
        assert page.locator(SELECTORS["import_existing_row"]).count() == 1
        notification = page.locator(SELECTORS["patrimonio_notification"]).filter(
            has_text="Atualização concluída. Revise posições antes de confirmar"
        )
        assert notification.is_visible()
        assert notification.get_attribute("role") == "status"
        _capture(page, ARTIFACT_PATH)

        page.click(SELECTORS["import_cancel_btn"])
        page.wait_for_selector(SELECTORS["import_modal_overlay"], state="hidden")
        page.wait_for_function(
            "() => document.querySelector('[data-testid=\"patrimonio-actions\"]')"
            ".dataset.syncState === 'idle'"
        )
        sync_button = page.locator(SELECTORS["dashboard_sync_btn"])
        assert "sync-success" not in (
            page.locator(SELECTORS["patrimonio_actions"]).get_attribute("class") or ""
        )
        assert sync_button.get_attribute("aria-busy") is None
        assert page.locator(SELECTORS["patrimonio_notification"]).count() == 0
        assert page.evaluate("document.activeElement?.dataset.testid") == "dashboard-sync-btn"

    def test_notification_manual_close_and_focus_pause(self, page: Page, live_url: str) -> None:
        _login(page, live_url)
        notification = page.locator(SELECTORS["patrimonio_notification"]).first
        notification.hover()
        page.wait_for_timeout(8_100)
        assert notification.is_visible()
        assert page.locator(SELECTORS["patrimonio_notification_close"]).get_attribute(
            "aria-label"
        ) == ("Fechar notificação")
        page.click(SELECTORS["patrimonio_notification_close"])
        assert page.locator(SELECTORS["patrimonio_notification"]).count() == 0

    def test_loading_blocks_duplicate_click(self, page: Page, live_url: str) -> None:
        _login(page, live_url)
        calls: list[str] = []

        def start(route: Route) -> None:
            calls.append(route.request.method)
            route.fulfill(status=202, json={"job_id": "job-loading", "status": "queued"})

        page.route("**/api/myprofit/sync", start)
        page.click(SELECTORS["dashboard_sync_btn"])
        page.wait_for_function(
            "() => document.querySelector('[data-testid=\"dashboard-sync-btn\"]')?.disabled"
        )
        page.evaluate(
            "document.querySelector('[data-testid=\"dashboard-sync-btn\"]')"
            ".dispatchEvent(new MouseEvent('click', {bubbles: true}))"
        )
        assert calls == ["POST"]
        _capture(page, ARTIFACT_DIR / "f60-atualizar-posicao-loading.png")

    def test_failed_job_keeps_modal_closed(self, page: Page, live_url: str) -> None:
        _login(page, live_url)

        page.route(
            "**/api/myprofit/sync",
            lambda route: route.fulfill(
                status=202, json={"job_id": "job-failed", "status": "queued"}
            ),
        )
        page.route(
            "**/api/myprofit/sync/*",
            lambda route: route.fulfill(
                status=200,
                json={
                    "job_id": "job-failed",
                    "status": "failed",
                    "preview": None,
                    "error": {"message": "Não foi possível baixar o CSV do MyProfit."},
                },
            ),
        )
        page.click(SELECTORS["dashboard_sync_btn"])
        page.wait_for_function(
            "() => document.querySelector('[data-testid=\"patrimonio-actions\"]')"
            ".dataset.syncState === 'error'",
            timeout=8_000,
        )
        assert not page.locator(SELECTORS["import_modal_overlay"]).is_visible()
        notification = page.locator(SELECTORS["patrimonio_notification"]).filter(
            has_text="Não foi possível baixar o CSV do MyProfit."
        )
        assert notification.is_visible()
        assert notification.get_attribute("role") == "alert"
        assert notification.get_attribute("aria-live") == "assertive"
        _capture(page, ARTIFACT_DIR / "f60-atualizar-posicao-error.png")

    def test_expired_job_keeps_modal_closed(self, page: Page, live_url: str) -> None:
        _login(page, live_url)
        page.route(
            "**/api/myprofit/sync",
            lambda route: route.fulfill(
                status=202, json={"job_id": "job-expired", "status": "queued"}
            ),
        )
        page.route(
            "**/api/myprofit/sync/*",
            lambda route: route.fulfill(
                status=200,
                json={"job_id": "job-expired", "status": "expired", "preview": None, "error": None},
            ),
        )
        page.click(SELECTORS["dashboard_sync_btn"])
        page.wait_for_function(
            "() => document.querySelector('[data-testid=\"patrimonio-actions\"]')"
            ".dataset.syncState === 'error'",
            timeout=8_000,
        )
        assert not page.locator(SELECTORS["import_modal_overlay"]).is_visible()

    def test_malformed_success_is_error(self, page: Page, live_url: str) -> None:
        _login(page, live_url)
        page.route(
            "**/api/myprofit/sync",
            lambda route: route.fulfill(status=202, json={"job_id": "job-bad", "status": "queued"}),
        )
        page.route(
            "**/api/myprofit/sync/*",
            lambda route: route.fulfill(
                status=200,
                json={"job_id": "job-bad", "status": "succeeded", "preview": {"preview_id": "x"}},
            ),
        )
        page.click(SELECTORS["dashboard_sync_btn"])
        page.wait_for_function(
            "() => document.querySelector('[data-testid=\"patrimonio-actions\"]')"
            ".dataset.syncState === 'error'",
            timeout=8_000,
        )
        assert not page.locator(SELECTORS["import_modal_overlay"]).is_visible()

    def test_family_sync_action_is_disabled(self, page: Page, live_url: str) -> None:
        _login(page, live_url)
        family_value = page.locator(SELECTORS["profile_option_family"]).get_attribute("value")
        assert family_value
        page.select_option(SELECTORS["profile_switcher"], family_value)
        page.wait_for_selector(SELECTORS["dashboard_sync_btn"], state="visible", timeout=8_000)
        button = page.locator(SELECTORS["dashboard_sync_btn"])
        assert button.is_disabled()
        assert button.get_attribute("data-sync-state") == "disabled"
        assert page.locator(SELECTORS["patrimonio_notifications"]).count() == 0
        assert page.locator(SELECTORS["import_modal_overlay"]).count() == 1
        _capture(page, ARTIFACT_DIR / "f60-atualizar-posicao-family.png")
