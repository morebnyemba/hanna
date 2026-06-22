import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { jwtDecode } from 'jwt-decode';

interface DecodedToken {
  role: 'admin' | 'client' | 'manufacturer' | 'technician' | 'retailer' | 'retailer_branch';
  exp: number;
}

// Backend role values use underscores; the retailer-branch portal's URL segment uses a hyphen.
const PORTAL_TO_ROLE: Record<string, string> = {
  'retailer-branch': 'retailer_branch',
};

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const authStateCookie = request.cookies.get('auth-storage');

  let role: string | null = null;
  if (authStateCookie) {
    try {
      const authState = JSON.parse(authStateCookie.value);
      const accessToken = authState?.state?.accessToken;
      if (accessToken) {
        const decodedToken: DecodedToken = jwtDecode(accessToken);
        if (decodedToken.exp * 1000 > Date.now()) {
          role = decodedToken.role;
        }
      }
    } catch (e) {
      console.error('Failed to parse auth cookie or decode token', e);
    }
  }

  const portal = pathname.split('/')[1]; // e.g., 'admin', 'client', 'retailer-branch'

  // If there's no role (or the token is missing/expired), redirect to login.
  if (!role) {
    const loginUrl = new URL(`/${portal}/login`, request.url);
    return NextResponse.redirect(loginUrl);
  }

  // An admin can access any portal.
  if (role === 'admin') {
    return NextResponse.next();
  }

  // For other roles, they must match the portal they are trying to access.
  const expectedRole = PORTAL_TO_ROLE[portal] ?? portal;
  if (role !== expectedRole) {
    const loginUrl = new URL(`/${portal}/login`, request.url);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

// See "Matching Paths" below to learn more
export const config = {
  // This matcher defines which routes the middleware will run on.
  // We use a negative lookahead to match all routes under a portal EXCEPT the login page.
  matcher: [
    '/admin/:path((?!login).*)',
    '/client/:path((?!login|claim).*)',
    '/manufacturer/:path((?!login).*)',
    '/technician/:path((?!login).*)',
    '/retailer/:path((?!login).*)',
    '/retailer-branch/:path((?!login).*)',
  ],
};