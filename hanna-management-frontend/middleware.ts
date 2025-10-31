import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Get the authentication token from the cookies.
  // Middleware cannot access localStorage, so we must use cookies.
  const authToken = request.cookies.get('accessToken')?.value;

  // If the user is trying to access a protected route without a token,
  // redirect them to the login page.
  if (!authToken) {
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }

  // If the user is authenticated, allow them to proceed.
  return NextResponse.next();
}

// See "Matching Paths" below to learn more
export const config = {
  // This matcher defines which routes the middleware will run on.
  // Here, it protects the '/dashboard' route and any sub-routes.
  matcher: [
    '/admin/dashboard/:path*',
    '/client/dashboard/:path*',
    '/manufacturer/dashboard/:path*',
    '/technician/dashboard/:path*',
  ],
};