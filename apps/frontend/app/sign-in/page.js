import SignInButton from "./SignInButton";
import WorkspaceBrand from "../WorkspaceBrand";

export const metadata = {
  title: "Sign in — Acadence",
  description: "Sign in to your Acadence account with Google.",
};

export default function SignInPage() {
  return (
    <main id="main-content" className="auth-page" tabIndex={-1}>
      <div className="auth-layout">
        <section className="auth-intro" aria-labelledby="sign-in-title">
          <WorkspaceBrand />
          <div className="auth-hero-body">
            <div className="auth-hero-art">
              <img
                src="/illustrations/ai-mentor/robo-girl-auth-hero.svg"
                alt="Acadence AI Mentor robot illustration"
                className="auth-hero-image"
              />
              <span className="illustration-label">AI illustration</span>
            </div>
            <div className="auth-hero-copy">
              <p className="section-kicker">Welcome to Acadence</p>
              <h1 id="sign-in-title">A thoughtful start for your report.</h1>
              <p className="auth-description">
                Sign in to return to your workspace. Your project details stay
                yours to review and confirm.
              </p>
            </div>
          </div>
        </section>

        <section
          className="auth-card acadence-card"
          aria-labelledby="auth-options-title"
        >
          <p className="auth-card-kicker">Your account</p>
          <h2 id="auth-options-title">Welcome back</h2>
          <p className="auth-description">
            Sign in with the Google account linked to your Acadence workspace.
          </p>
          <SignInButton />
          <div className="auth-unavailable">
            <div className="auth-option-heading">
              <h3>Mobile OTP</h3>
              <span className="auth-status">Not available yet</span>
            </div>
            <button
              aria-describedby="otp-unavailable-note"
              className="auth-otp-button"
              type="button"
              disabled
            >
              Continue with mobile OTP
            </button>
            <p className="auth-option-note" id="otp-unavailable-note">
              Phone sign-in is not available in this release.
            </p>
          </div>
          <p className="auth-privacy-note">
            Sign-in is handled securely through Google. Your workspace is
            protected by your Acadence session.
          </p>
        </section>
      </div>
    </main>
  );
}
