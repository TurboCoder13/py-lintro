# typed: false
# frozen_string_literal: true

# Homebrew formula for lintro binary distribution
# This installs a pre-compiled binary that doesn't require Python
class LintroBin < Formula
  desc "Unified CLI for code quality (binary)"
  homepage "https://github.com/lgtm-hq/py-lintro"
  version "0.22.0"
  license "MIT"

  RELEASE_BASE = "https://github.com/lgtm-hq/py-lintro/releases"

  on_macos do
    on_arm do
      url "#{RELEASE_BASE}/download/v#{version}/lintro-macos-arm64"
      sha256 "PLACEHOLDER_ARM64_SHA256"
    end
    on_intel do
      url "#{RELEASE_BASE}/download/v#{version}/lintro-macos-x86_64"
      sha256 "PLACEHOLDER_X86_64_SHA256"
    end
  end

  def install
    if Hardware::CPU.arm?
      bin.install "lintro-macos-arm64" => "lintro"
    else
      bin.install "lintro-macos-x86_64" => "lintro"
    end
  end

  def caveats
    <<~EOS
      lintro-bin is a standalone binary that doesn't require Python.

      However, the external tools must be installed separately.
      Install them via Homebrew:
        brew install ruff black mypy bandit biome rust \\
          hadolint actionlint gitleaks markdownlint-cli2 prettier \\
          yamllint semgrep shellcheck shfmt sqlfluff taplo

      After installing rust, add clippy and rustfmt via rustup:
        rustup component add clippy rustfmt

      Optional Rust tools (install via cargo):
        cargo install cargo-audit

      Or for Python tools via pipx:
        pipx install ruff black mypy bandit pydoclint yamllint sqlfluff semgrep

      For the Python-based version with bundled tools, use:
        brew install lgtm-hq/tap/lintro
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/lintro --version")
    assert_match "Usage:", shell_output("#{bin}/lintro --help")
  end
end
