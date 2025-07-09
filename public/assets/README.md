# Assets Directory

This directory contains static assets for the Aviation Traceability System public files.

## Directory Structure

```
assets/
├── images/          # Image files (logos, icons, backgrounds)
├── documents/       # PDF documents, user guides, etc.
├── fonts/           # Custom font files
└── data/           # JSON data files, configuration files
```

## Usage Examples

### Images
- Logo: `/public/assets/images/logo.png`
- Icons: `/public/assets/images/icons/`
- Backgrounds: `/public/assets/images/backgrounds/`

### Documents
- User Guide: `/public/assets/documents/user-guide.pdf`
- API Documentation: `/public/assets/documents/api-docs.pdf`

### Fonts
- Custom fonts: `/public/assets/fonts/custom-font.woff2`

### Data Files
- Configuration: `/public/assets/data/config.json`
- Sample data: `/public/assets/data/sample-certificates.json`

## File Size Recommendations

- **Images**: Optimize for web (< 1MB per image)
- **Documents**: Keep PDFs under 10MB
- **Fonts**: Use modern formats (WOFF2, WOFF)
- **Data**: Keep JSON files under 500KB

## Supported Formats

### Images
- PNG, JPG, JPEG, WebP, SVG
- GIF for animations
- ICO for favicons

### Documents
- PDF for documentation
- TXT for plain text files
- MD for markdown files

### Fonts
- WOFF2 (preferred)
- WOFF
- TTF, OTF (fallback)

## Security Notes

- All files in this directory are publicly accessible
- Do not store sensitive information
- Regularly audit uploaded files
- Use appropriate file permissions 