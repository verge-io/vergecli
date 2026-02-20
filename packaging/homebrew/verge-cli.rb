# Template Homebrew formula for verge-cli.
#
# The canonical formula lives at: verge-io/homebrew-tap/Formula/verge-cli.rb
#
# To update after a new PyPI release:
#   1. pip install homebrew-pypi-poet
#   2. poet -f verge-cli          # generates resource stanzas
#   3. Update url, sha256, and resource stanzas in the tap formula
#   4. brew audit --strict verge-cli
#   5. Push to verge-io/homebrew-tap

class VergeCli < Formula
  include Language::Python::Virtualenv

  desc "Command-line interface for VergeOS infrastructure management"
  homepage "https://github.com/verge-io/verge-cli"
  url "https://files.pythonhosted.org/packages/source/v/verge-cli/verge_cli-1.0.0.tar.gz"
  sha256 "PLACEHOLDER"
  license "Apache-2.0"

  depends_on "python@3.12"

  # Resource stanzas go here. Generate with:
  #   poet -f verge-cli
  #
  # Example:
  #   resource "pyvergeos" do
  #     url "https://files.pythonhosted.org/packages/..."
  #     sha256 "..."
  #   end

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/vrg --version")
  end
end
