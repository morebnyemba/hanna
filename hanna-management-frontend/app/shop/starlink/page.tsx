import CategoryShopLayout from '../_components/CategoryShopLayout';
import { STARLINK_CONFIG } from '../_config/categories';

export const metadata = { title: 'Starlink — Hanna Shop' };

export default function StarlinkPage() {
  return <CategoryShopLayout config={STARLINK_CONFIG} />;
}
