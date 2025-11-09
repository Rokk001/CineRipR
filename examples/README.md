# CineRipR Examples

This directory contains example configurations and deployment files for CineRipR.

## 📁 Contents

### Configuration Files

- **[cineripr.toml.example](cineripr.toml.example)** - Example configuration file with all available options
  - Copy to `cineripr.toml` and adjust paths for your setup
  - Contains comments explaining each option

### Docker Deployment

- **[docker-compose.yml](docker-compose.yml)** - Docker Compose configuration example
  - Production-ready setup with all recommended settings
  - Includes health checks, logging, and volume mappings
  - Both full and minimal configuration examples

## 🚀 Quick Start

### Using Docker Compose

1. Copy the example files:
   ```bash
   cp examples/docker-compose.yml ./docker-compose.yml
   cp examples/cineripr.toml.example ./cineripr.toml
   ```

2. Edit `cineripr.toml` with your paths:
   ```toml
   [paths]
   download_roots = ["/path/to/downloads"]
   extracted_root = "/path/to/extracted"
   finished_root = "/path/to/finished"
   ```

3. Adjust volume mappings in `docker-compose.yml`

4. Start the container:
   ```bash
   docker-compose up -d
   ```

5. Access the WebGUI at `http://localhost:8080`

### Using Configuration File Directly

```bash
# Copy and edit configuration
cp examples/cineripr.toml.example /path/to/config/cineripr.toml

# Run CineRipR
cineripr --config /path/to/config/cineripr.toml
```

## 📚 Additional Resources

- [Main Documentation](../docs/) - Complete project documentation
- [Docker Permissions Guide](../docs/operations/docker-permissions.md) - Detailed Docker setup
- [GitHub Repository](https://github.com/Rokk001/CineRipR) - Source code and issues

## 💡 Tips

- **User/Group IDs**: Set to match your file system permissions (e.g., `99:100` for Unraid)
- **Umask**: Use `umask 000` for full read/write permissions
- **WebGUI**: Access at port 8080 by default (configurable)
- **Volumes**: Ensure all mapped directories exist and have proper permissions

## 🐛 Troubleshooting

If you encounter issues:

1. Check container logs: `docker logs cineripr`
2. Verify file permissions on mapped volumes
3. Ensure 7-Zip is working: `docker exec cineripr 7z`
4. Check the [operations documentation](../docs/operations/) for common issues

## 🤝 Contributing

Found a better configuration? Submit a pull request with:
- Clear description of improvements
- Use case explanation
- Testing notes

See [Contributing Guide](../docs/development/contributing.md) for more details.

