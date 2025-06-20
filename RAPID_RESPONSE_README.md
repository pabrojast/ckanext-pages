# Rapid Response and Recovery Extension

## Overview

This extension adds a new endpoint to ckanext-pages specifically designed for documenting emergency response and disaster recovery activities. It provides a structured format similar to ArcGIS StoryMaps and Copernicus Rapid Mapping for UNESCO's rapid response documentation.

## Features

- **Structured Format**: Pre-defined sections for disaster information, key facts, map stories, and additional content
- **Interactive Maps**: Support for embedding iframes from ArcGIS, Copernicus, and other mapping platforms
- **Image Galleries**: Carousel sections for disaster-related imagery
- **Key Information Boxes**: Highlighted sections for critical disaster data
- **Responsive Design**: Works well on desktop and mobile devices

## Usage

### Accessing Rapid Response Pages

- **List all pages**: `/rapid-response`
- **View specific page**: `/rapid-response/{page-name}`
- **Create new page**: `/rapid-response_edit`
- **Edit existing page**: `/rapid-response_edit/{page-name}`

### Creating a New Rapid Response Page

1. Navigate to `/rapid-response_edit`
2. Fill in the basic information:
   - **URL**: Unique identifier for the page (auto-generated from title)
   - **Disaster Title**: Main title (e.g., "Cyclone Idai Floods and Landslides")
   - **Subtitle**: Additional disaster information
   - **Event Date**: Date of the disaster event
   - **Visibility**: Public or Private

3. Complete the structured sections:

#### Key Information Box
Add critical disaster data in a highlighted blue box:
```markdown
**Event Date**: Start: 4 March 2019, End: 21 March 2019

**Countries Affected**: Mozambique, Madagascar, Malawi, Zimbabwe

**UNESCO Designated Sites**:
- World Heritage Sites: none
- Biosphere Reserves: Chimanimani Biosphere Reserve
```

#### Main Content
Detailed information about the disaster and response. Supports HTML and iframes:
```html
## Introduction

In response to the Cyclone Idai...

<iframe src="https://your-map-url" width="100%" height="400"></iframe>
```

#### Map Stories
Interactive maps and spatial analysis:
```markdown
### Floods
Risk classification for infrastructure...

### Landslides  
More than 10,000 new landslides were identified...

<iframe src="https://arcgis-story-map-url" width="100%" height="500"></iframe>
```

#### Image Gallery
Disaster-related images:
```markdown
![Satellite image](https://example.com/satellite-image.jpg)
![Impact assessment](https://example.com/impact-image.jpg)
```

#### Additional Content
Additional sections like school safety assessments, recovery plans, etc.

### Example Structure

Based on the provided HTML example, a typical rapid response page might include:

1. **Header**: Disaster title with optional custom header image
2. **Key Information Box**: Essential disaster facts and figures
3. **Main Content**: Detailed description and response activities
4. **Image Gallery**: Visual documentation of the disaster
5. **Map Stories**: Interactive maps showing impacts, risks, and assessments
6. **Additional Sections**: Specialized content like VISUS school assessments

### Navigation

The new rapid response pages appear in the main navigation menu alongside regular pages and blog posts. They are treated as a separate content type with their own URL structure and templates.

### Permissions

- **View**: Public pages can be viewed by anyone, private pages require appropriate permissions
- **Create/Edit**: Requires `ckanext_pages_update` permission
- **Delete**: Requires `ckanext_pages_delete` permission

## Technical Implementation

### New Page Type
- Pages are stored with `page_type='rapid-response'`
- Uses existing ckanext-pages infrastructure with additional fields stored in `extras`

### Additional Fields
- `subtitle`: Disaster subtitle
- `key_info`: Key information box content
- `image_carousel`: Image gallery content
- `map_stories`: Map stories section
- `additional_content`: Additional sections
- `header_image`: Custom header image URL
- `excerpt`: Summary for list pages

### Templates
- `rapid-response.html`: Main display template
- `rapid-response_list.html`: List view template
- `rapid-response_edit.html`: Edit form template
- `rapid-response_revisions.html`: Revision history
- `rapid-response_revisions_preview.html`: Revision preview

### CSS Styling
Custom CSS provides UNESCO-themed styling with:
- Blue color scheme (#467886)
- Responsive design
- Special formatting for key information boxes
- Map container styling
- Print-friendly styles

## Installation

This extension is built on top of ckanext-pages. Ensure ckanext-pages is properly installed and configured before using the rapid response functionality.

The rapid response features are automatically available once ckanext-pages is installed with this enhanced version.

## Example Content

For testing and demonstration purposes, you can create a rapid response page for "Cyclone Idai Floods and Landslides" using the structure provided in the HTML example from the request folder. 