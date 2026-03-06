#!/bin/bash
# Setup script to help configure Git for pushing to GitHub

set -e

echo "🔧 Git Push Setup Helper"
echo "========================"
echo ""

# Check if SSH key exists
if [ -f ~/.ssh/id_ed25519 ] || [ -f ~/.ssh/id_rsa ]; then
    echo "✓ SSH key found"

    # Display public key
    if [ -f ~/.ssh/id_ed25519.pub ]; then
        echo ""
        echo "📋 Your SSH public key (add this to GitHub):"
        echo "-------------------------------------------"
        cat ~/.ssh/id_ed25519.pub
        echo "-------------------------------------------"
    elif [ -f ~/.ssh/id_rsa.pub ]; then
        echo ""
        echo "📋 Your SSH public key (add this to GitHub):"
        echo "-------------------------------------------"
        cat ~/.ssh/id_rsa.pub
        echo "-------------------------------------------"
    fi

    echo ""
    echo "📝 To add this key to GitHub:"
    echo "1. Go to: https://github.com/settings/keys"
    echo "2. Click 'New SSH key'"
    echo "3. Paste the key above"
    echo "4. Click 'Add SSH key'"

else
    echo "⚠ No SSH key found. Generating new key..."
    echo ""

    read -p "Enter your GitHub email: " email

    ssh-keygen -t ed25519 -C "$email" -f ~/.ssh/id_ed25519 -N ""

    echo ""
    echo "✓ SSH key generated!"
    echo ""
    echo "📋 Your new SSH public key (add this to GitHub):"
    echo "-------------------------------------------"
    cat ~/.ssh/id_ed25519.pub
    echo "-------------------------------------------"
    echo ""
    echo "📝 To add this key to GitHub:"
    echo "1. Go to: https://github.com/settings/keys"
    echo "2. Click 'New SSH key'"
    echo "3. Paste the key above"
    echo "4. Click 'Add SSH key'"
fi

echo ""
echo "🧪 Testing GitHub connection..."

# Start SSH agent if not running
if ! pgrep -x "ssh-agent" > /dev/null; then
    eval "$(ssh-agent -s)"
fi

# Add key to agent
if [ -f ~/.ssh/id_ed25519 ]; then
    ssh-add ~/.ssh/id_ed25519 2>/dev/null || true
elif [ -f ~/.ssh/id_rsa ]; then
    ssh-add ~/.ssh/id_rsa 2>/dev/null || true
fi

# Test connection
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo "✓ GitHub SSH authentication working!"
    echo ""
    echo "🚀 You're ready to push!"
    echo "   Run: git push origin main"
else
    echo "⚠ GitHub SSH not authenticated yet"
    echo "   Make sure you've added the SSH key to GitHub"
    echo "   Then run: git push origin main"
fi

echo ""
echo "📦 Current git status:"
git status -sb
