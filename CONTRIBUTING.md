# Contributing to Blender Animations Plugin

Thank you for your interest in contributing! Here's how to get involved.

## 🐛 Reporting Bugs

1. Check [existing issues](../../issues) first to avoid duplicates
2. Open a new issue with:
   - Blender version
   - Roblox Studio version / plugin version
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots or video if applicable

## 💡 Suggesting Features

Open a GitHub Issue with the `enhancement` label and describe:
- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered

## 🔧 Submitting Pull Requests

1. Fork the repository
2. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes following the code style below
4. Test thoroughly in Blender and Roblox Studio
5. Commit with clear messages:
   ```bash
   git commit -m "feat: add bone filter for R6 rigs"
   ```
6. Push and open a Pull Request against `main`

## 🐍 Python Code Style (Blender Addon)

- Follow **PEP 8** conventions
- Use **Blender Python API** (`bpy`) idioms
- All operators must have a `bl_idname`, `bl_label`, and `bl_description`
- Panels must define `bl_space_type`, `bl_region_type`, `bl_category`
- Test in **Blender 3.6 LTS**, **4.1**, and **4.2 LTS**

## 📜 License

By contributing, you agree that your contributions will be licensed under **GPL-3.0**.
