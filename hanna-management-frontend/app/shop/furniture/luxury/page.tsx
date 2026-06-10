import CategoryShopLayout from '../../_components/CategoryShopLayout';
import { FURNITURE_LUXURY_CONFIG } from '../../_config/categories';

export const metadata = { title: 'Luxury Furniture — Hanna Shop' };

export default function LuxuryFurniturePage() {
  return <CategoryShopLayout config={FURNITURE_LUXURY_CONFIG} />;
}
