# AI Chat Frontend

A modern chat application built with SvelteKit, featuring real-time communication and AI integration.

## Features

- Real-time chat using WebSocket
- Authentication with JWT
- Conversation management
- AI model integration
- Responsive design with Tailwind CSS
- TypeScript support

## Prerequisites

- Node.js 16+
- npm or yarn
- Backend API running on `http://localhost:8000`

## Setup

1. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

2. Create a `.env` file in the root directory with the following variables:
   ```
   VITE_API_URL=http://localhost:8000/api/v1
   VITE_WS_URL=ws://localhost:8000
   ```

3. Start the development server:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. Open `http://localhost:3000` in your browser.

## Project Structure

```
frontend/
├── src/
│   ├── lib/
│   │   ├── components/     # UI components
│   │   ├── stores/        # Svelte stores
│   │   ├── services/      # API and WebSocket services
│   │   └── types/         # TypeScript types
│   ├── routes/
│   │   ├── (auth)/        # Authentication routes
│   │   └── (app)/         # Protected routes
│   └── app.config.ts      # SvelteKit configuration
├── static/                # Static assets
└── tests/                # Test files
```

## Development

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run test` - Run tests
- `npm run lint` - Run linter
- `npm run format` - Format code

## Testing

The project uses Vitest for unit testing and Playwright for end-to-end testing.

```bash
# Run unit tests
npm run test

# Run e2e tests
npm run test:e2e
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT
