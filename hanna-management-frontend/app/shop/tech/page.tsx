import CategoryShopLayout from '../_components/CategoryShopLayout';
import { TECH_CONFIG } from '../_config/categories';

export const metadata = { title: 'Tech & Electronics — Hanna Shop' };

export default function TechPage() {
  return <CategoryShopLayout config={TECH_CONFIG} />;
}
