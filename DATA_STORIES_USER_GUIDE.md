# Data Stories Editor - Quick Start Guide

## Overview

The Data Stories editor has been modernized with a modular block system inspired by Rapid Response, featuring rich text editing, Terria map integration, media embeds, and image uploads.

## Key Features

### 1. Section Management

**Create Sections:**
- Click "Add Section" button at bottom of sections area
- Enter a descriptive section title
- Choose section type from dropdown (Introduction, Methodology, Results, etc.)

**Organize Sections:**
- Use ↑ ↓ buttons in section header to reorder sections
- Click trash icon to remove a section
- Sections auto-number in the form

### 2. Content Blocks

Each section can contain multiple content blocks:

#### Text Blocks
- **Purpose**: Rich formatted text content
- **Features**: 
  - Headers (H2, H3)
  - Bold, italic, underline
  - Bullet and numbered lists
  - Links and images
  - Clean formatting
- **How to Add**: Click "Text Block" button
- **Editor**: Quill WYSIWYG editor with toolbar

#### Terria Map Blocks
- **Purpose**: Interactive Terria map visualizations
- **Features**:
  - Paste Terria share links
  - Optional title for the map
  - Live preview before saving
  - Full-width responsive iframe
- **How to Add**: Click "Terria Map" button
- **Configuration**: 
  1. Paste your Terria share link (e.g., `https://ihp-wins.unesco.org/terria/#share=abc123`)
  2. Add optional title
  3. Click "Preview Map" to see it live

#### Media/Iframe Blocks
- **Purpose**: Videos, external content, custom iframes
- **Features**:
  - YouTube URL auto-detection
  - Custom iframe embed code support
  - Configurable width and height
  - Live preview
- **How to Add**: Click "Media/Iframe" button
- **Supported Formats**:
  - YouTube URLs (automatically converted to embeds)
  - Direct iframe/embed code
  - Any URL (wrapped in iframe)

### 3. Image Gallery

**Upload Images:**
1. Navigate to "Image Gallery" section
2. Drag & drop images onto the dropzone, OR
3. Click dropzone to browse and select files

**Manage Images:**
- **Preview**: Thumbnail preview shown immediately
- **Alt Text**: Add descriptive alt text for accessibility
- **Caption**: Optional caption for the image
- **Copy URL**: Click to copy image URL to clipboard
- **Delete**: Click trash icon to remove

**Using Images:**
- Copy the image URL from the gallery
- In a text block, use the image insert tool
- Paste the copied URL

### 4. Block Operations

**Reorder Blocks:**
- Each block has ↑ ↓ buttons
- Click to move block up or down within the section
- Changes save when you submit the form

**Delete Blocks:**
- Click trash icon on any block
- Confirm deletion in popup
- Block removed immediately

**Preview Blocks:**
- Terria and Media blocks have "Preview" buttons
- Click to show/hide inline preview
- Verify content before saving

## Workflow Example

### Creating a Complete Story Section

1. **Add Section**
   ```
   Click "Add Section" → Title: "Study Results" → Type: "Results"
   ```

2. **Add Introduction Text**
   ```
   Click "Text Block" → Write overview of results
   Format with headers, bold key findings
   ```

3. **Add Terria Map**
   ```
   Click "Terria Map" → Paste share link
   Add title: "Spatial Distribution of Water Resources"
   Preview to verify
   ```

4. **Add Explanation Text**
   ```
   Click "Text Block" → Describe what the map shows
   Reference specific features
   ```

5. **Add Supporting Media**
   ```
   Click "Media/Iframe" → Add YouTube video or chart
   Set appropriate dimensions
   Preview to check
   ```

6. **Upload Supporting Images**
   ```
   Go to Image Gallery → Upload screenshots
   Add alt text and captions
   Reference in text blocks if needed
   ```

## Design Features

### UNESCO Styling
- Professional blue color palette (#0072BC)
- Gradient backgrounds
- Smooth animations
- Consistent spacing and typography

### Responsive Design
- Works on desktop, tablet, and mobile
- Touch-friendly controls
- Optimized for different screen sizes

### User Feedback
- Loading indicators during uploads
- Success messages when copying URLs
- Hover effects on all interactive elements
- Clear visual hierarchy

## Tips & Best Practices

### Content Organization
- Use descriptive section titles
- Group related content in the same section
- Use multiple text blocks instead of one large block
- Place visualizations after explanatory text

### Images
- Use descriptive filenames
- Always add alt text for accessibility
- Keep file sizes reasonable (<10MB)
- Use appropriate image formats (JPG for photos, PNG for graphics)

### Maps
- Test share links before adding
- Use descriptive titles
- Consider map load time
- Ensure Terria instance is accessible

### Media
- Verify embed codes work
- Set appropriate dimensions
- Test videos play correctly
- Consider mobile viewing experience

## Keyboard Shortcuts

Currently, the editor uses mouse/touch interactions. Standard browser shortcuts work in text editors:
- **Ctrl/Cmd + B**: Bold
- **Ctrl/Cmd + I**: Italic
- **Ctrl/Cmd + K**: Insert link
- **Ctrl/Cmd + Z**: Undo
- **Ctrl/Cmd + Y**: Redo

## Troubleshooting

### Images not uploading
- Check file size (<10MB)
- Verify file format (JPG, PNG, GIF)
- Check internet connection
- Try smaller files

### Terria map not showing
- Verify share link is complete
- Check if Terria instance is accessible
- Try preview first
- Ensure URL starts with https://

### YouTube video not embedding
- Use full YouTube URL (not shortened youtu.be)
- Check video is public/embeddable
- Try the embed code from YouTube directly

### Content not saving
- Check all required fields are filled
- Verify no JavaScript errors in console
- Try again after refreshing page
- Check network connectivity

## Support

For technical issues or feature requests, contact the CKAN development team or check the repository documentation.

## Changes from Old Editor

### What's New
- ✨ Rich text editing (was plain textarea)
- ✨ Multiple blocks per section (was single content field)
- ✨ Visual Terria map preview (was just URL field)
- ✨ Image upload gallery (was not available)
- ✨ Media block support (was limited)
- ✨ Drag & drop uploads (was not available)
- ✨ Live previews (was not available)

### What's the Same
- Section types and structure
- Form validation
- SEO metadata fields
- Slug auto-generation
- Organization selection
- Save/Cancel buttons

### Backward Compatibility
- Old stories load correctly
- Data structure preserved
- No migration needed
- Existing features work as before
