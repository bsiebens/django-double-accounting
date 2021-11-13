import graphene

from .api import currency


class Mutation(currency.Mutation, graphene.ObjectType):
    pass


class Query(currency.Query, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
