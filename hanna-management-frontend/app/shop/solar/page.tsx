import CategoryShopLayout from '../_components/CategoryShopLayout';
import { SOLAR_CONFIG } from '../_config/categories';

export const metadata = { title: 'Solar Products — Hanna Shop' };

export default function SolarPage() {
  return <CategoryShopLayout config={SOLAR_CONFIG} />;
}
