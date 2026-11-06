# NATIONVK AVIATOR RESEARCH LAB — Android

## Build
The GitHub Actions workflow `.github/workflows/android-apk.yml` builds a debug APK on pushes to Android project files or on manual dispatch. Download the artifact named `aviator-research-lab-debug-apk` from the workflow run.

## Screen OCR
1. Install and open the app.
2. Tap **Start screen capture / OCR**.
3. Android shows its own MediaProjection consent screen. Choose the screen/app sharing option and confirm.
4. Keep the app being observed visible in the captured display. OCR looks for visible values formatted like `1.23x` and sends recognized values to the local research dashboard.
5. Tap **Stop capture** to end the foreground capture service.

Android requires explicit user consent for every screen-capture session. A persistent notification indicates active capture. The app does not bypass app protections, scrape private APIs, or place bets.

## Known limitations
- OCR accuracy depends on screen layout, language, resolution, animations and visibility. It may miss or misread values.
- The current parser recognizes multiplier-like text ending in x/×; it is a prototype, not a verified Aviator integration.
- It does not know whether an OCR value is the current round or a historical value shown elsewhere. Validate imported observations before statistical analysis.
- Android may stop capture when the user revokes permission, the app is stopped, or the OS ends the projection.
- This is an unsigned debug APK. A release APK needs a securely managed signing key.

## Research integrity
Screen capture supplies observations, not secret seeds or future outcomes. No prediction accuracy is guaranteed. Do not use results as betting advice.
