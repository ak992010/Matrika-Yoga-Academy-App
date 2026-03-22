Matrika Academy Live Wrapper (Android)
Android WebView wrapper for the Matrika Academy Streamlit app.

How it works
- Debug builds load the local Streamlit server at `http://10.0.2.2:8501`.
- Release builds read the URL from `app/src/main/res/values/strings.xml`.
- The app name is `Matrika Academy` and the provided logo is used as the launcher icon.

What to change for production
- Edit `app/src/main/res/values/strings.xml` and replace `streamlit_url` with your deployed HTTPS URL.
- Keep the release URL on HTTPS for Play Store submission.
- Replace `app/src/main/res/drawable/matrika_logo.png` if you want a different brand icon.

Build
1) Open this folder in Android Studio.
2) Sync Gradle.
3) Run the debug app to test against your local Streamlit server.
4) Build a signed AAB/APK for release after updating the production URL.
