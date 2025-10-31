import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { jwtDecode } from 'jwt-decode';

interface DecodedToken {
  role: 'admin' | 'client' | 'manufacturer' | 'technician';
  exp: number;
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const authStateCookie = request.cookies.get('auth-storage');
  
  let role: string | null = null;
  if (authStateCookie) {
    try {
      const authState = JSON.parse(authStateCookie.value);
      const accessToken = authState?.state?.accessToken;
      if (accessToken) {
        const decodedToken: DecodedToken = jwtDecode(accessToken);
        role = decodedToken.role;
      }
    } catch (e) {
      console.error('Failed to parse auth cookie or decode token', e);
    }
  }

  const portal = pathname.split('/')[1]; // e.g., 'admin', 'client'

  if (!role || role !== portal) {
    const loginUrl = new URL(`/${portal}/login`, request.url);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

// See "Matching Paths" below to learn more
export const config = {
  // This matcher defines which routes the middleware will run on.
  matcher: [
    '/admin/dashboard/:path*',
    '/client/dashboard/:path*',
    '/manufacturer/dashboard/:path*',
    '/technician/dashboard/:path*',
  ],
};