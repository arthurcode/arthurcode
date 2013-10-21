from haystack import indexes
from models import Product


class ProductIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return Product

    def index_queryset(self, using=None):
        """
        Index active products.
        """
        return self.get_model().active.all()