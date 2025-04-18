from django.test import TestCase
from django.core.cache import cache
from django.contrib.gis.geos import Point
from rest_framework.test import APIClient
from rest_framework import status
from .models import Property, Portfolio
from .serializers import PropertySerializer

class PropertyViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.portfolio1 = Portfolio.objects.create(name="Oslo Portfolio")
        self.portfolio2 = Portfolio.objects.create(name="Bergen Portfolio")

        self.property1 = Property.objects.create(
            portfolio=self.portfolio1,
            name="Karl Johans gate 1",
            address="Karl Johans gate 1",
            zip_code="0154",
            city="Oslo",
            location=Point(10.7522, 59.9139),
            estimated_value=25000000,
            relevant_risks=5,
            handled_risks=3,
            total_financial_risk=1200000
        )

        self.property2 = Property.objects.create(
            portfolio=self.portfolio2,
            name="Torgallmenningen 1",
            address="Torgallmenningen 1",
            zip_code="5014",
            city="Bergen",
            location=Point(5.3242, 60.3913),
            estimated_value=15000000,
            relevant_risks=3,
            handled_risks=1,
            total_financial_risk=800000
        )

    def test_list_properties(self):
        response = self.client.get('/api/properties/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('type' in response.json())
        self.assertTrue('features' in response.json())
        self.assertEqual(len(response.json()['features']), 2)

    def test_filter_properties_by_portfolio(self):
        response = self.client.get(f'/api/properties/?portfolio={self.portfolio1.pk}', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['features']), 1)
        self.assertEqual(response.json()['features'][0]['properties']['name'], "Karl Johans gate 1")

    def test_filter_properties_by_bbox(self):
        response = self.client.get('/api/properties/?in_bbox=10.7,59.9,10.8,60.0', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['features']), 1)
        self.assertEqual(response.json()['features'][0]['properties']['name'], "Karl Johans gate 1")

    def test_filter_properties_by_bbox_and_portfolio(self):
        url = f'/api/properties/?in_bbox=10.7,59.9,10.8,60.0&portfolio={self.portfolio1.pk}'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['features']), 1)

    def test_empty_bbox_results(self):
        response = self.client.get('/api/properties/?in_bbox=0,0,1,1', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['features']), 0)

    def test_create_property(self):
        data = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [10.7271, 59.9111]
            },
            'properties': {
                'portfolio': self.portfolio1.pk,
                'name': 'Aker Brygge 12',
                'address': 'Stranden 1',
                'zip_code': '0250',
                'city': 'Oslo',
                'estimated_value': 45000000,
                'relevant_risks': 4,
                'handled_risks': 2,
                'total_financial_risk': 2100000
            }
        }
        response = self.client.post('/api/properties/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Property.objects.count(), 3)

    def test_get_single_property(self):
        response = self.client.get(f'/api/properties/{self.property1.pk}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['properties']['name'], "Karl Johans gate 1")

    def test_update_property(self):
        data = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [10.7522, 59.9139]
            },
            'properties': {
                'portfolio': self.portfolio1.pk,
                'name': 'Updated Name',
                'address': self.property1.address,
                'zip_code': self.property1.zip_code,
                'city': self.property1.city,
                'estimated_value': self.property1.estimated_value,
                'relevant_risks': self.property1.relevant_risks,
                'handled_risks': self.property1.handled_risks,
                'total_financial_risk': self.property1.total_financial_risk
            }
        }
        response = self.client.put(f'/api/properties/{self.property1.pk}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property1.refresh_from_db()
        self.assertEqual(self.property1.name, 'Updated Name')

    def test_delete_property(self):
        response = self.client.delete(f'/api/properties/{self.property1.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Property.objects.count(), 1)

class PortfolioViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.portfolio = Portfolio.objects.create(name="Oslo Portfolio")

    def test_list_portfolios(self):
        response = self.client.get('/api/portfolios/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_create_portfolio(self):
        data = {'name': 'Bergen Portfolio'}
        response = self.client.post('/api/portfolios/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Portfolio.objects.count(), 2)

    def test_get_single_portfolio(self):
        response = self.client.get(f'/api/portfolios/{self.portfolio.pk}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], "Oslo Portfolio")

    def test_update_portfolio(self):
        data = {'name': 'Updated Portfolio'}
        response = self.client.put(f'/api/portfolios/{self.portfolio.pk}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.portfolio.refresh_from_db()
        self.assertEqual(self.portfolio.name, 'Updated Portfolio')

    def test_delete_portfolio(self):
        response = self.client.delete(f'/api/portfolios/{self.portfolio.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Portfolio.objects.count(), 0)

class ThrottleTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()

    def test_property_throttling(self):
        for _ in range(100):
            response = self.client.get('/api/properties/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get('/api/properties/')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_portfolio_throttling(self):
        for _ in range(100):
            response = self.client.get('/api/portfolios/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get('/api/portfolios/')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def tearDown(self):
        cache.clear()

class SerializerValidationTests(TestCase):
    def setUp(self):
        self.portfolio = Portfolio.objects.create(name="Test Portfolio")
        self.valid_property_data = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [10.7522, 59.9139]
            },
            'properties': {
                'portfolio': self.portfolio.pk,
                'name': 'Test Property',
                'address': 'Test Street 1',
                'zip_code': '0154',
                'city': 'Oslo',
                'estimated_value': 1000000,
                'relevant_risks': 5,
                'handled_risks': 3,
                'total_financial_risk': 100000
            }
        }

    def test_name_validation(self):
        data = self.valid_property_data.copy()
        data['properties']['name'] = ''
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

        data['properties']['name'] = 'a' * 101
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_zip_code_validation(self):
        data = self.valid_property_data.copy()
        data['properties']['zip_code'] = '123'
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('zip_code', serializer.errors)

        data['properties']['zip_code'] = '12345'
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('zip_code', serializer.errors)

        data['properties']['zip_code'] = 'abcd'
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('zip_code', serializer.errors)

    def test_handled_risks_validation(self):
        data = self.valid_property_data.copy()
        data['properties']['relevant_risks'] = 3
        data['properties']['handled_risks'] = 5
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_location_validation(self):
        data = self.valid_property_data.copy()
        data['geometry']['coordinates'] = [181, 0]
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('location', serializer.errors)

        data['geometry']['coordinates'] = [0, 91]
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('location', serializer.errors)

    def test_estimated_value_validation(self):
        data = self.valid_property_data.copy()
        data['properties']['estimated_value'] = -1000
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('estimated_value', serializer.errors)

        data['properties']['estimated_value'] = 2000000000
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('estimated_value', serializer.errors)

    def test_city_validation(self):
        data = self.valid_property_data.copy()
        data['properties']['city'] = ''
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('city', serializer.errors)

        data['properties']['city'] = 'a' * 101
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('city', serializer.errors)

    def test_address_validation(self):
        data = self.valid_property_data.copy()
        data['properties']['address'] = ''
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('address', serializer.errors)

        data['properties']['address'] = 'a' * 256
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('address', serializer.errors)

    def test_risks_number_validation(self):
        data = self.valid_property_data.copy()
        data['properties']['relevant_risks'] = -1
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('relevant_risks', serializer.errors)

        data['properties']['relevant_risks'] = 1001
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('relevant_risks', serializer.errors)

        data = self.valid_property_data.copy()
        data['properties']['handled_risks'] = -1
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('handled_risks', serializer.errors)

    def test_financial_risk_validation(self):
        data = self.valid_property_data.copy()
        data['properties']['total_financial_risk'] = -1
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('total_financial_risk', serializer.errors)

        data['properties']['total_financial_risk'] = 1000000001
        serializer = PropertySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('total_financial_risk', serializer.errors)
