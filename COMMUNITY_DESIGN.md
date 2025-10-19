# Ripple Communities - Visual Design Guide

## Color Palette

### Primary Colors
- **Blue**: `#3B82F6` (bg-blue-500, bg-blue-600)
- **Purple**: `#A855F7` (for gradients)
- **Green**: `#10B981` (for success states)
- **Gray**: Various shades for text and borders

### Gradients
- **Avatar Gradient**: Blue-400 to Purple-500
- **Header Gradient**: Blue-500 to Purple-600

## Component Designs

### 1. Community Card (Grid View)

**Structure**:
```
┌────────────────────────────────────────┐
│  ┌──┐ Community Name                   │
│  │[P]│ 👥 25 members                   │
│  └──┘                                   │
│                                         │
│  A vibrant community for Python        │
│  lovers of all levels...               │
│                                         │
│  [Python]                               │
│                                         │
│  📅 2 days ago        [View/Joined]    │
└────────────────────────────────────────┘
```

**Specifications**:
- **Card Size**: Flexible width, auto height
- **Padding**: 1rem (p-4)
- **Border**: 1px solid gray-200
- **Hover**: Shadow-md, subtle scale
- **Avatar**: 48px circle with gradient background
- **Badge**: Blue-100 bg, blue-700 text, rounded

### 2. Community Header (Detail Page)

**Structure**:
```
┌──────────────────────────────────────────────────┐
│  ╔════════════════════════════════════════════╗ │
│  ║ Gradient Background (Blue → Purple)         ║ │
│  ║                                             ║ │
│  ║  ┌────┐                                     ║ │
│  ║  │ [P]│  Community Name                     ║ │
│  ║  │    │  👥 25 members  [Python]   [Join]  ║ │
│  ║  └────┘                                     ║ │
│  ║                                             ║ │
│  ║  Full community description here with      ║ │
│  ║  details about what the community is...    ║ │
│  ║                                             ║ │
│  ║  👤 Created by @username · 2 days ago      ║ │
│  ╚════════════════════════════════════════════╝ │
└──────────────────────────────────────────────────┘
```

**Specifications**:
- **Background**: Gradient (blue-500 to purple-600)
- **Text**: White text for contrast
- **Padding**: 2rem (p-8)
- **Avatar**: 80px circle, white background
- **Button**: White bg with blue text, or green for join

### 3. Navigation Tabs

**Structure**:
```
┌──────────────────────────────────────────┐
│ Discussion | Members | Resources | About │
│ ──────────                                │
└──────────────────────────────────────────┘
```

**Specifications**:
- **Active Tab**: Blue-500 bottom border (2px), blue-600 text
- **Inactive Tab**: Gray-500 text, transparent border
- **Hover**: Gray-700 text
- **Font**: Medium weight

### 4. Member Grid

**Structure**:
```
┌────────────────────────────────────────────┐
│ Members (25)                                │
│                                             │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │
│  │ [A]  │ │ [B]  │ │ [C]  │ │ [D]  │     │
│  │Alice │ │ Bob  │ │Carol │ │Dave  │     │
│  │      │ │Creator│ │      │ │      │     │
│  └──────┘ └──────┘ └──────┘ └──────┘     │
│                                             │
│           View all 25 members →            │
└────────────────────────────────────────────┘
```

**Specifications**:
- **Grid**: 2 cols mobile, 4 tablet, 6 desktop
- **Avatar**: 64px circle
- **Spacing**: 1rem gap between items
- **Hover**: Gray-50 background

### 5. Discussion Post

**Structure**:
```
┌─────────────────────────────────────────┐
│  ┌──┐ Username · 2 hours ago            │
│  │[U]│                                   │
│  └──┘ Post content goes here...         │
│                                          │
│       👍 Like  💬 Comment  🔗 Share     │
└─────────────────────────────────────────┘
```

**Specifications**:
- **Border**: 1px solid gray-200
- **Padding**: 1rem (p-4)
- **Avatar**: 40px circle
- **Action Buttons**: Gray-500, hover blue-600
- **Icon Size**: 16px (h-4 w-4)

## Responsive Breakpoints

### Mobile (< 768px)
- **Grid**: 1 column for communities
- **Member Grid**: 2 columns
- **Font Sizes**: Slightly smaller headings

### Tablet (768px - 1024px)
- **Grid**: 2 columns for communities
- **Member Grid**: 4 columns
- **Standard spacing**

### Desktop (> 1024px)
- **Grid**: 3 columns for communities
- **Member Grid**: 6 columns
- **Maximum width**: Container-based

## Iconography

Using **Heroicons** (outline style):

- **Members/Users**: User-group icon
- **Time/Date**: Calendar icon
- **Comments**: Chat-bubble icon
- **Likes**: Thumb-up icon
- **Share**: Share icon
- **Lock/Private**: Lock-closed icon

## Typography

### Font Family
- System font stack (default Tailwind)
- `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, ...`

### Font Sizes
- **Page Heading**: 2xl (1.5rem) - bold
- **Card Title**: lg (1.125rem) - semibold
- **Body Text**: sm (0.875rem) - regular
- **Meta Text**: xs (0.75rem) - regular
- **Detail Heading**: 3xl (1.875rem) - bold

### Font Weights
- **Bold**: 700 (headings)
- **Semibold**: 600 (subheadings, buttons)
- **Medium**: 500 (tabs, labels)
- **Regular**: 400 (body text)

## Interactive States

### Hover States
- **Cards**: Shadow increase (shadow-md), subtle scale
- **Buttons**: Darker shade (e.g., blue-600 → blue-700)
- **Links**: Text color change (gray → blue)
- **Member Cards**: Background gray-50

### Active States
- **Tabs**: Bottom border + color change
- **Selected Filter**: Distinct styling
- **Joined Badge**: Green background

### Focus States
- **Inputs**: Ring-2 ring-blue-500
- **Buttons**: Ring-2 ring-offset-2

## Spacing System

### Margins & Padding
- **Tight**: 0.25rem (1)
- **Small**: 0.5rem (2)
- **Medium**: 1rem (4)
- **Large**: 1.5rem (6)
- **XLarge**: 2rem (8)

### Gap Spacing
- **Cards Grid**: 1.5rem (gap-6)
- **Elements**: 0.75rem (gap-3)
- **Tight Elements**: 0.25rem (gap-1)

## Animations

### Transitions
- **Duration**: 150ms (transition-colors, transition-shadow)
- **Easing**: Default (ease)
- **Properties**: colors, shadow, transform

### Hover Effects
```css
.card:hover {
  box-shadow: md;
  transform: translateY(-2px);
}
```

## Accessibility

### Color Contrast
- Ensure WCAG AA compliance (4.5:1 for normal text)
- White text on dark backgrounds (gradients)
- Dark text on light backgrounds

### Focus Indicators
- Visible focus rings on all interactive elements
- Skip links for keyboard navigation

### Screen Readers
- Semantic HTML elements
- ARIA labels where needed
- Alt text for avatars

## Best Practices

1. **Consistency**: Use the same spacing, colors, and components throughout
2. **Hierarchy**: Clear visual hierarchy with size, weight, and color
3. **Feedback**: Visual feedback for all interactions
4. **Performance**: Optimize images, use CSS transitions
5. **Mobile-First**: Design for mobile, enhance for desktop
6. **Loading States**: Show loading indicators for async operations
7. **Error Handling**: Clear error messages with helpful icons

## Example Color Codes

```css
/* Primary Actions */
--primary-blue: #3B82F6;
--primary-blue-dark: #2563EB;

/* Success */
--success-green: #10B981;
--success-green-light: #D1FAE5;

/* Neutral */
--gray-50: #F9FAFB;
--gray-100: #F3F4F6;
--gray-200: #E5E7EB;
--gray-500: #6B7280;
--gray-700: #374151;
--gray-900: #111827;

/* Gradients */
--gradient-avatar: linear-gradient(135deg, #60A5FA, #A855F7);
--gradient-header: linear-gradient(90deg, #3B82F6, #9333EA);
```

## Implementation Notes

- All components use Tailwind CSS utility classes
- Responsive design uses Tailwind breakpoints (md:, lg:)
- SVG icons from Heroicons library
- Form inputs have focus states
- Buttons have hover and active states
- Cards have subtle animations on hover

