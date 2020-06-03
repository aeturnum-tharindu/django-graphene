import graphene
from graphene import relay
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import Movie, Director

import graphql_jwt
from graphql_jwt.decorators import  login_required
from graphql_relay import from_global_id


class MovieType(DjangoObjectType):
    class Meta:
        model = Movie

    movie_generation = graphene.String()

    def resolve_movie_generation(self, info):
        return "New Movie" if self.year > 2005 else "Old Movie"


# Relay implementation
class MovieNode(DjangoObjectType):
    class Meta:
        model = Movie
        filter_fields = {
            'title': ['exact', 'icontains'],
            'year': ['exact', ]
         }
        interfaces = (relay.Node, )


class DirectorType(DjangoObjectType):
    class Meta:
        model = Director


class Query(graphene.ObjectType):
    # all_movies = graphene.List(MovieType)
    all_movies = DjangoFilterConnectionField(MovieNode)
    # movie = graphene.Field(MovieType, id=graphene.Int(), title=graphene.String())
    movie = relay.Node.Field(MovieNode)

    all_directors = graphene.List(DirectorType)
    director = graphene.Field(DirectorType, id=graphene.Int(), name=graphene.String())

    # @login_required
    # def resolve_all_movies(self, info):
    #     return Movie.objects.all()

    # def resolve_movie(self, info,  **kwargs):
    #     id = kwargs.get("id")
    #     title = kwargs.get("title")
    #
    #     if id is not None:
    #         return Movie.objects.get(pk=id)
    #
    #     if title is not None:
    #         return Movie.objects.get(title=title)
    #
    #     return None

    def resolve_all_directors(self, info):
        return Director.objects.all()

    def resolve_director(self, info, id=None, name=None):
        if id is not None:
            return Director.objects.get(pk=id)

        if name is not None:
            return Director.objects.get(name=name)

        return None

class MovieCreateMutation(graphene.Mutation):
    class Arguments:
        title = graphene.String()
        year = graphene.Int()

    movie = graphene.Field(MovieType)

    def mutate(self, info, title, year):
        movie = Movie.objects.create(title=title, year=year)

        return MovieCreateMutation(movie=movie)


class MovieUpdateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        title = graphene.String()
        year = graphene.Int()

    movie = graphene.Field(MovieType)

    def mutate(self, info, id, title, year):
        movie = Movie.objects.get(pk=id)

        if title is not None:
            movie.title = title
        if year is not None:
            movie.year = year

        movie.save()

        return MovieUpdateMutation(movie=movie)


class MovieUpdateMutationRelay(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)
        title = graphene.String()

    movie = graphene.Field(MovieType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, id, title):
        movie = Movie.objects.get(pk =from_global_id(id)[1])

        if title is not None:
            movie.title = title

        movie.save()

        return MovieUpdateMutationRelay(movie=movie)


class MovieDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    movie = graphene.Field(MovieType)

    def mutate(self, info, id):
        movie = Movie.objects.get(pk=id)
        movie.delete()

        return MovieDeleteMutation(movie=None)


class DirectorCreateMutation(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        surname = graphene.String(required=True)

    director = graphene.Field(DirectorType)

    def mutate(self, info, name, surname):
        dir = Director.objects.create(name=name, surname=surname)

        return DirectorCreateMutation(director=dir)


class Mutation:
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()

    # Movie related CRUD ops
    create_movie = MovieCreateMutation.Field()
    update_movie = MovieUpdateMutation.Field()
    update_movie_relay = MovieUpdateMutationRelay.Field()
    delete_movie = MovieDeleteMutation.Field()

    # Director related CRUD ops
    create_director = DirectorCreateMutation.Field()
