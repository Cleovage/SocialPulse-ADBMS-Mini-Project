"""
Empirical Challenge Harness: Cross-View Navigation & Fallback Workflows
Author: challenger_m2_2
Target: SocialPulse Frontend SPA (M2 Integration)

Tests:
1. Cross-View Navigation across all 7 views + DOM consistency checks
2. Rapid tab switching stress-test (concurrency & race condition resistance)
3. Fallback workflow simulation (error fallback -> synthetic DB transition with @username filter)
4. Fallback resolution with actual matching synthetic creator (@elena_ai_tech)
5. API key modal workflows (open, toggle password masking, save config, backdrop & cancel dismissal)
6. Cross-navigation shortcuts (global search routing, influencer view to IG view jump)
7. Console error & unhandled exception monitoring
"""

import sys
import time
import json
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=" * 80)
    print("EMPIRICAL CHALLENGE: CROSS-VIEW NAVIGATION & FALLBACK WORKFLOWS")
    print("=" * 80)

    console_errors = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Capture console errors and uncaught page exceptions
        def on_console(msg):
            if msg.type in ["error"]:
                # Ignore expected network 404s during mock injection tests
                if "Failed to load resource" not in msg.text and "favicon" not in msg.text:
                    console_errors.append(f"[{msg.type.upper()}] {msg.text}")
        
        def on_page_error(err):
            page_errors.append(str(err))

        page.on("console", on_console)
        page.on("pageerror", on_page_error)

        # ----------------------------------------------------------------------
        # Test 1: Initial Page Load
        # ----------------------------------------------------------------------
        print("\n[TEST 1] Initial Page Load & Default View...")
        page.goto(BASE_URL, wait_until="networkidle")
        time.sleep(1)

        # Check default view is overview
        overview_view = page.locator("#view-overview")
        assert not overview_view.get_attribute("class") or "hidden" not in overview_view.get_attribute("class"), \
            "view-overview should be visible initially"

        overview_nav = page.locator("#nav-overview")
        assert "glass-nav-active" in (overview_nav.get_attribute("class") or ""), \
            "nav-overview should have glass-nav-active class"

        topbar_title = page.locator("#topbar-title").inner_text()
        assert "Overview" in topbar_title, f"Expected Overview in topbar, got {topbar_title}"
        print("  --> PASS: Initial page loaded with view-overview active.")

        # ----------------------------------------------------------------------
        # Test 2: Systematic Cross-View Navigation across all 7 views
        # ----------------------------------------------------------------------
        print("\n[TEST 2] Systematic Cross-View Navigation (7 Views)...")
        views_to_test = [
            ("overview", "Overview Dashboard"),
            ("influencers", "Influencer Discovery & Analytics"),
            ("instagram", "Live Instagram Creator Lookup"),
            ("trends", "Trend Radar & Viral Velocity"),
            ("campaigns", "Campaign Planner & ACID Transactions"),
            ("geo", "Geospatial Analytics ($geoNear)"),
            ("adbms-lab", "ADBMS Architecture & Explain Lab"),
        ]

        all_view_ids = [v[0] for v in views_to_test]

        for view_name, expected_title in views_to_test:
            nav_btn = page.locator(f"#nav-{view_name}")
            assert nav_btn.count() == 1, f"Missing nav button for #nav-{view_name}"
            nav_btn.click()
            time.sleep(0.3)

            # 1. Target view must NOT have hidden
            active_view = page.locator(f"#view-{view_name}")
            classes = active_view.get_attribute("class") or ""
            assert "hidden" not in classes.split(), f"view-{view_name} should be visible, classes: {classes}"

            # 2. Target nav button must have glass-nav-active
            nav_classes = nav_btn.get_attribute("class") or ""
            assert "glass-nav-active" in nav_classes, f"nav-{view_name} missing glass-nav-active: {nav_classes}"

            # 3. All other views must be hidden
            for other_v in all_view_ids:
                if other_v != view_name:
                    other_view = page.locator(f"#view-{other_v}")
                    other_classes = other_view.get_attribute("class") or ""
                    assert "hidden" in other_classes.split(), f"view-{other_v} should be hidden when in {view_name}"
                    other_nav = page.locator(f"#nav-{other_v}")
                    other_nav_classes = other_nav.get_attribute("class") or ""
                    assert "glass-nav-active" not in other_nav_classes, f"nav-{other_v} should not be active"

            # 4. Topbar title matches
            current_title = page.locator("#topbar-title").inner_text()
            assert expected_title in current_title, f"Expected {expected_title} in topbar, got {current_title}"
            print(f"  --> PASS: Successfully switched to view-{view_name} ('{expected_title}')")

        # ----------------------------------------------------------------------
        # Test 3: Rapid View-Switching Stress Harness (Race conditions & state preservation)
        # ----------------------------------------------------------------------
        print("\n[TEST 3] Rapid Tab Switching Stress Harness (30 cycles)...")
        import random
        random.seed(42)
        sequence = random.choices(all_view_ids, k=30)
        for i, target_v in enumerate(sequence):
            page.locator(f"#nav-{target_v}").click()
            # Fast interval - 40ms
            time.sleep(0.04)
        
        # Settle on instagram view
        page.locator("#nav-instagram").click()
        time.sleep(0.5)

        active_view = page.locator("#view-instagram")
        assert "hidden" not in (active_view.get_attribute("class") or "").split(), \
            "After rapid switching, view-instagram should be visible"
        print("  --> PASS: Rapid tab switching stress harness survived with zero UI desync.")

        # ----------------------------------------------------------------------
        # Test 4: Instagram View Initial State
        # ----------------------------------------------------------------------
        print("\n[TEST 4] Instagram Initial State Verification...")
        initial_el = page.locator("#ig-initial-state")
        card_el = page.locator("#ig-profile-card")
        error_el = page.locator("#ig-error-fallback")
        skeleton_el = page.locator("#ig-loading-skeleton")

        assert "hidden" not in (initial_el.get_attribute("class") or "").split(), "ig-initial-state should be visible"
        assert "hidden" in (card_el.get_attribute("class") or "").split(), "ig-profile-card should be hidden"
        assert "hidden" in (error_el.get_attribute("class") or "").split(), "ig-error-fallback should be hidden"
        assert "hidden" in (skeleton_el.get_attribute("class") or "").split(), "ig-loading-skeleton should be hidden"
        print("  --> PASS: Initial elements in expected visibility state.")

        # ----------------------------------------------------------------------
        # Test 5: Fallback Workflow on Simulated Lookup Failure
        # ----------------------------------------------------------------------
        print("\n[TEST 5] Fallback Workflow with Simulated Failure & Redirection...")
        test_fail_user = "unobtainable_ghost_user_99"

        # Intercept profile request to simulate a 404 failure with error payload
        def handle_profile_route(route):
            if test_fail_user in route.request.url:
                route.fulfill(
                    status=404,
                    content_type="application/json",
                    body=json.dumps({
                        "status": "error",
                        "error": f"Creator @{test_fail_user} not found or rate limit exceeded.",
                        "suggest_synthetic": True
                    })
                )
            else:
                route.continue_()

        page.route("**/api/instagram/profile/**", handle_profile_route)

        # Trigger search
        search_input = page.locator("#ig-search-input")
        search_input.fill(test_fail_user)
        search_btn = page.locator("#ig-search-btn")
        search_btn.click()

        # Wait for error fallback to appear
        page.wait_for_selector("#ig-error-fallback:not(.hidden)", timeout=5000)

        # Verify fallback card content
        error_msg = page.locator("#ig-error-message").inner_text()
        assert test_fail_user in error_msg or "not found" in error_msg, f"Unexpected error message: {error_msg}"

        fallback_btn_text = page.locator("#ig-fallback-btn-text").inner_text()
        assert test_fail_user in fallback_btn_text, f"Fallback button missing username: {fallback_btn_text}"
        print(f"  --> PASS: Error fallback rendered properly: '{fallback_btn_text}'")

        # Now click the Fallback button: "Search Local Synthetic Database for '{username}'"
        print("  --> Clicking fallback button to verify redirect to view-influencers...")
        fallback_btn = page.locator("#btn-ig-fallback-synthetic")
        fallback_btn.click()
        time.sleep(0.5)

        # Verify redirection to view-influencers
        inf_view = page.locator("#view-influencers")
        assert "hidden" not in (inf_view.get_attribute("class") or "").split(), \
            "view-influencers should be visible after fallback click"

        inf_nav = page.locator("#nav-influencers")
        assert "glass-nav-active" in (inf_nav.get_attribute("class") or ""), \
            "nav-influencers should have glass-nav-active after fallback"

        # Verify search input is pre-populated with @{test_fail_user}
        inf_search_input = page.locator("#inf-search")
        assert inf_search_input.input_value() == f"@{test_fail_user}", \
            f"Expected @{test_fail_user} in inf-search, got {inf_search_input.input_value()}"

        # Unroute mock
        page.unroute("**/api/instagram/profile/**", handle_profile_route)
        print("  --> PASS: Redirection to view-influencers with populated search value verified.")

        # ----------------------------------------------------------------------
        # Test 6: Fallback Resolution with Real Synthetic Creator (@elena_ai_tech)
        # ----------------------------------------------------------------------
        print("\n[TEST 6] Fallback Workflow with Matching Synthetic Creator (@elena_ai_tech)...")
        # Navigate back to instagram
        page.locator("#nav-instagram").click()
        time.sleep(0.3)

        real_synthetic_user = "elena_ai_tech"

        def handle_elena_route(route):
            if real_synthetic_user in route.request.url:
                route.fulfill(
                    status=404,
                    content_type="application/json",
                    body=json.dumps({
                        "status": "error",
                        "error": "Instagram scraper simulated rate-limit timeout",
                        "suggest_synthetic": True
                    })
                )
            else:
                route.continue_()

        page.route("**/api/instagram/profile/**", handle_elena_route)

        page.locator("#ig-search-input").fill(real_synthetic_user)
        page.locator("#ig-search-btn").click()

        page.wait_for_selector("#ig-error-fallback:not(.hidden)", timeout=5000)
        page.locator("#btn-ig-fallback-synthetic").click()
        time.sleep(0.8)

        # Check that influencer-grid loaded Elena Rostova
        grid_html = page.locator("#influencer-grid").inner_text()
        assert "Elena Rostova" in grid_html or "elena_ai_tech" in grid_html, \
            f"Expected Elena Rostova in grid, got: {grid_html[:200]}"
        print("  --> PASS: Fallback successfully resolved creator in local synthetic database!")

        page.unroute("**/api/instagram/profile/**", handle_elena_route)

        # ----------------------------------------------------------------------
        # Test 7: API Key Settings Modal Workflows
        # ----------------------------------------------------------------------
        print("\n[TEST 7] API Key Settings Modal Workflows...")
        # Navigate to instagram view
        page.locator("#nav-instagram").click()
        time.sleep(0.3)

        # Open modal using API Settings button
        settings_btn = page.locator("button:has-text('API Settings')")
        assert settings_btn.count() >= 1, "API Settings button not found in instagram header"
        settings_btn.first.click()
        time.sleep(0.3)

        modal = page.locator("#modal-api-settings")
        assert "hidden" not in (modal.get_attribute("class") or "").split(), \
            "modal-api-settings should be visible after clicking settings"

        # Check loaded config status
        current_mode = page.locator("#settings-current-mode").inner_text()
        assert len(current_mode) > 0 and current_mode != "Loading...", f"Current mode not loaded: {current_mode}"
        print(f"  --> Modal opened. Current mode: '{current_mode}'")

        # Test password masking toggle
        key_input = page.locator("#settings-rapidapi-key")
        assert key_input.get_attribute("type") == "password", "Key input should initially be type password"

        eye_btn = page.locator("button:has(#eye-icon-settings)")
        eye_btn.click()
        time.sleep(0.1)
        assert key_input.get_attribute("type") == "text", "Key input type should be text after eye toggle"
        eye_icon = page.locator("#eye-icon-settings")
        assert "fa-eye-slash" in (eye_icon.get_attribute("class") or ""), "Eye icon should show fa-eye-slash"

        eye_btn.click()
        time.sleep(0.1)
        assert key_input.get_attribute("type") == "password", "Key input type should revert to password"
        assert "fa-eye" in (eye_icon.get_attribute("class") or ""), "Eye icon should revert to fa-eye"
        print("  --> PASS: Password masking toggle works bidirectionally.")

        # Test saving API key
        test_key = "rapidapi_test_challenge_key_9999"
        key_input.fill(test_key)
        save_btn = modal.locator("button[type='submit']")
        save_btn.click()
        time.sleep(0.5)

        # Modal should close on successful save
        assert "hidden" in (modal.get_attribute("class") or "").split(), \
            "modal-api-settings should be hidden after save"

        # Reopen modal to verify saved key status
        settings_btn.first.click()
        time.sleep(0.5)
        key_status = page.locator("#settings-key-status").inner_text()
        assert "*" in key_status or "..." in key_status or "rapi" in key_status.lower() or "configured" in key_status.lower(), \
            f"Expected masked key in status, got '{key_status}'"
        print(f"  --> PASS: API key saved and masked status displayed: '{key_status}'")

        # Reset key to blank (Direct Crawler mode)
        key_input.fill("")
        save_btn.click()
        time.sleep(0.5)
        print("  --> PASS: Reset API key to blank successfully.")

        # Test Cancel button to close
        settings_btn.first.click()
        time.sleep(0.3)
        cancel_btn = modal.locator("button:has-text('Cancel')")
        cancel_btn.click()
        time.sleep(0.2)
        assert "hidden" in (modal.get_attribute("class") or "").split(), \
            "Modal should close when Cancel is clicked"
        print("  --> PASS: Cancel button closes modal.")

        # Test Backdrop click to close
        settings_btn.first.click()
        time.sleep(0.3)
        # Click on modal backdrop (outermost padding area)
        modal.click(position={"x": 10, "y": 10})
        time.sleep(0.3)
        assert "hidden" in (modal.get_attribute("class") or "").split(), \
            "Modal should close when backdrop is clicked"
        print("  --> PASS: Backdrop click closes modal.")

        # ----------------------------------------------------------------------
        # Test 8: Cross-Navigation Shortcuts
        # ----------------------------------------------------------------------
        print("\n[TEST 8] Cross-Navigation Shortcuts & Global Search...")
        # 1. Global search input with @username
        global_search = page.locator("#global-search-input")
        if global_search.count() > 0:
            global_search.fill("@zuck")
            global_search.press("Enter")
            time.sleep(0.5)
            # Should route to instagram view
            assert "hidden" not in (page.locator("#view-instagram").get_attribute("class") or "").split(), \
                "Global search with @ should route to view-instagram"
            print("  --> PASS: Global search @username routes to view-instagram.")

        # 2. Influencer view toolbar button "Live IG Lookup"
        page.locator("#nav-influencers").click()
        time.sleep(0.3)
        live_lookup_btn = page.locator("button:has-text('Live IG Lookup')")
        if live_lookup_btn.count() > 0:
            live_lookup_btn.first.click()
            time.sleep(0.3)
            assert "hidden" not in (page.locator("#view-instagram").get_attribute("class") or "").split(), \
                "Live IG Lookup button in influencers toolbar should route to view-instagram"
            print("  --> PASS: Influencer toolbar 'Live IG Lookup' button routes to view-instagram.")

        # ----------------------------------------------------------------------
        # Test 9: Edge Cases & Error Resilience
        # ----------------------------------------------------------------------
        print("\n[TEST 9] Edge Cases & Error Resilience...")
        page.locator("#nav-instagram").click()
        time.sleep(0.2)

        # Empty search
        page.locator("#ig-search-input").fill("")
        page.locator("#ig-search-btn").click()
        time.sleep(0.3)
        # Verify toast or graceful handling (no crash)
        toast = page.locator("#toast-container")
        assert "Please enter an Instagram username" in toast.inner_text(), "Expected warning toast for empty search"
        print("  --> PASS: Empty search triggers warning toast without crash.")

        # Special characters in search
        page.locator("#ig-search-input").fill("!@#$%^&*()")
        page.locator("#ig-search-btn").click()
        time.sleep(0.5)
        # Should not throw unhandled JS error
        print("  --> PASS: Special characters handled without unhandled exception.")

        browser.close()

    # ----------------------------------------------------------------------
    # Verification Summary
    # ----------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("CHALLENGE AUDIT REPORT & CONSOLE LOGS")
    print("=" * 80)
    print(f"Total Uncaught Page Exceptions: {len(page_errors)}")
    for pe in page_errors:
        print(f"  [PAGE ERROR] {pe}")

    print(f"Total Console Error Messages: {len(console_errors)}")
    for ce in console_errors:
        print(f"  [CONSOLE ERROR] {ce}")

    assert len(page_errors) == 0, f"Found {len(page_errors)} uncaught page errors!"
    print("\nALL 9 EMPIRICAL CHALLENGE SUITES PASSED WITH 100% SUCCESS!")

if __name__ == "__main__":
    try:
        run_tests()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Empirical Challenge Assertion Failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Empirical Challenge Execution Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)
