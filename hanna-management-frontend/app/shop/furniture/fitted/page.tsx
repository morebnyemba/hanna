import CategoryShopLayout from '../../_components/CategoryShopLayout';
import { FURNITURE_FITTED_CONFIG } from '../../_config/categories';

export const metadata = { title: 'Fitted Furniture — Hanna Shop' };

export default function FittedFurniturePage() {
  return <CategoryShopLayout config={FURNITURE_FITTED_CONFIG} />;
}
